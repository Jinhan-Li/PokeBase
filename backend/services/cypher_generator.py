# backend/services/cypher_generator.py
"""根据用户问题生成 Cypher 查询语句"""

import logging
import re

from services.llm_service import call_llm
from services.schema_provider import get_schema

logger = logging.getLogger(__name__)

CYPHER_PROMPT = """
你是一个宝可梦知识图谱的 Cypher 查询专家。根据用户的问题，生成对应的 Cypher 查询语句。

这是你需要的基本知识：

## 1. 概览

```
节点总数：  2,269
  - Pokemon:  1,025
  - Type:        18
  - Ability:    307
  - Move:       919

关系总数：82,313
  - HAS_TYPE:     2,470
  - HAS_ABILITY:  2,411
  - CAN_LEARN:   78,512
  - DAMAGE_TO:      120
```

---

## 2. 节点（Node）

### 2.1 Pokemon

| 属性 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | Integer | 全国图鉴编号 | `1` |
| `name` | String | 英文名（小写） | `"bulbasaur"` |
| `height` | Integer | 身高（分米） | `7` |
| `weight` | Integer | 体重（百克） | `69` |
| `base_experience` | Integer | 基础经验值 | `64` |

**数量**：1,025

**示例**：
```cypher
MATCH (p:Pokemon {name: "pikachu"})
RETURN p.id, p.name, p.height, p.weight, p.base_experience
-- 结果: 25, "pikachu", 4, 60, 112
```

### 2.2 Type

| 属性 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | Integer | 属性编号 | `13` |
| `name` | String | 英文名（小写） | `"electric"` |

**数量**：18

**完整列表**：

| id | name | id | name |
|----|------|----|------|
| 1 | normal | 10 | fire |
| 2 | fighting | 11 | water |
| 3 | flying | 12 | grass |
| 4 | poison | 13 | electric |
| 5 | ground | 14 | psychic |
| 6 | rock | 15 | ice |
| 7 | bug | 16 | dragon |
| 8 | ghost | 17 | dark |
| 9 | steel | 18 | fairy |

### 2.3 Ability

| 属性 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | Integer | 特性编号 | `9` |
| `name` | String | 英文名（小写） | `"static"` |

**数量**：307

### 2.4 Move

| 属性 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | Integer | 招式编号 | `85` |
| `name` | String | 英文名（小写） | `"thunderbolt"` |
| `power` | Integer | 威力 | `90` |
| `accuracy` | Integer | 命中率（%） | `100` |
| `pp` | Integer | 使用次数 | `15` |
| `priority` | Integer | 优先度 | `0` |

**数量**：919

---

## 3. 关系（Relationship）

### 3.1 HAS_TYPE

```
(Pokemon)-[:HAS_TYPE]->(Type)
```

- **数量**：2,470
- **说明**：每个 Pokemon 有 1~2 个属性
- **属性**：无

```cypher
-- 查看皮卡丘的属性
MATCH (p:Pokemon {name: "pikachu"})-[:HAS_TYPE]->(t:Type)
RETURN p.name, t.name
-- 结果: pikachu, electric
```

### 3.2 HAS_ABILITY

```
(Pokemon)-[:HAS_ABILITY]->(Ability)
```

- **数量**：2,411
- **说明**：每个 Pokemon 有 1~3 个特性（含隐藏特性）
- **属性**：无

```cypher
-- 查看小火龙的特性
MATCH (p:Pokemon {name: "charmander"})-[:HAS_ABILITY]->(a:Ability)
RETURN p.name, a.name
-- 结果: charmander → blaze, solar-power
```

### 3.3 CAN_LEARN

```
(Pokemon)-[:CAN_LEARN]->(Move)
```

- **数量**：78,512
- **说明**：Pokemon 可学会的招式（含升级、TM、遗传等所有来源）
- **属性**：无

```cypher
-- 查看皮卡丘能学的招式（前10个）
MATCH (p:Pokemon {name: "pikachu"})-[:CAN_LEARN]->(m:Move)
RETURN m.name LIMIT 10
```

### 3.4 HAS_TYPE（Move → Type）

```
(Move)-[:HAS_TYPE]->(Type)
```

- **说明**：招式的属性类型
- **属性**：无

```cypher
-- 查看十万伏特的属性
MATCH (m:Move {name: "thunderbolt"})-[:HAS_TYPE]->(t:Type)
RETURN m.name, t.name
-- 结果: thunderbolt, electric
```

### 3.5 DAMAGE_TO（属性克制）

```
(Type)-[:DAMAGE_TO {multiplier}]->(Type)
```

- **数量**：120
- **说明**：属性之间的伤害倍率关系
- **属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `multiplier` | Float | 伤害倍率 |

**倍率分布**：

| multiplier | 含义 | 数量 |
|------------|------|------|
| `2.0` | 双倍伤害（克制） | 51 |
| `0.5` | 一半伤害（抵抗） | 61 |
| `0.0` | 无效（免疫） | 8 |

```cypher
-- 火属性克制哪些属性？
MATCH (f:Type {name: "fire"})-[:DAMAGE_TO {multiplier: 2.0}]->(t:Type)
RETURN t.name
-- 结果: bug, steel, grass, ice

-- 什么属性克制水？
MATCH (f:Type)-[:DAMAGE_TO {multiplier: 2.0}]->(t:Type {name: "water"})
RETURN f.name
-- 结果: grass, electric

-- 水属性免疫哪些属性？（multiplier = 0.0 的情况）
MATCH (f:Type)-[:DAMAGE_TO {multiplier: 0.0}]->(t:Type)
RETURN f.name, t.name
```

---

## 4. 完整关系图

```
                    ┌──────────┐
                    │  Ability │
                    │ id, name │
                    └────▲─────┘
                         │
                    HAS_ABILITY
                         │
┌──────────┐        ┌────┴─────┐        ┌──────────┐
│   Type   │◄───────│ Pokemon  │───────►│   Move   │
│ id, name │HAS_TYPE│id,name,  │CAN_LEARN│id,name,  │
└────▲─────┘        │height,   │        │power,    │
     │              │weight,   │        │accuracy, │
     │              │base_exp  │        │pp,priority│
     │              └──────────┘        └────▲─────┘
     │                                       │
     │  DAMAGE_TO {multiplier}          HAS_TYPE
     │────────────────────────►              │
     │                                       │
     └───────────────────────────────────────┘
```

---

## 5. 命名规范

| 类别 | 规范 | 示例 |
|------|------|------|
| 节点标签 | PascalCase | `Pokemon`, `Type`, `Ability`, `Move` |
| 关系类型 | UPPER_SNAKE_CASE | `HAS_TYPE`, `CAN_LEARN`, `DAMAGE_TO` |
| 属性名 | snake_case | `base_experience`, `multiplier` |
| name 值 | 英文小写 + 连字符 | `"pikachu"`, `"speed-boost"`, `"thunderbolt"` |

**重要**：查询时 name 属性必须使用英文小写，如 `"pikachu"` 而非 `"Pikachu"` 或 `"皮卡丘"`。

---

## 6. 常用查询模板

### 实体查询

```cypher
-- 查 Pokemon 基本信息
MATCH (p:Pokemon {name: "pikachu"}) RETURN p

-- 查 Pokemon 的所有属性
MATCH (p:Pokemon {name: "pikachu"})-[:HAS_TYPE]->(t:Type) RETURN t.name

-- 查 Pokemon 的所有特性
MATCH (p:Pokemon {name: "pikachu"})-[:HAS_ABILITY]->(a:Ability) RETURN a.name

-- 查 Pokemon 的招式（限制数量）
MATCH (p:Pokemon {name: "pikachu"})-[:CAN_LEARN]->(m:Move) RETURN m.name LIMIT 20
```

### 属性克制

```cypher
-- A 属性克制哪些属性？
MATCH (t1:Type {name: "fire"})-[:DAMAGE_TO {multiplier: 2.0}]->(t2:Type) RETURN t2.name

-- 什么属性克制 B？
MATCH (t1:Type)-[:DAMAGE_TO {multiplier: 2.0}]->(t2:Type {name: "water"}) RETURN t1.name

-- A 对 B 的伤害倍率
MATCH (t1:Type {name: "fire"})-[r:DAMAGE_TO]->(t2:Type {name: "water"}) RETURN r.multiplier
```

### 招式查询

```cypher
-- 查招式的属性和威力
MATCH (m:Move {name: "thunderbolt"})-[:HAS_TYPE]->(t:Type)
RETURN m.name, m.power, m.accuracy, t.name

-- 查某属性的所有招式
MATCH (m:Move)-[:HAS_TYPE]->(t:Type {name: "fire"})
RETURN m.name, m.power ORDER BY m.power DESC LIMIT 10
```

### 统计查询

```cypher
-- 各属性 Pokemon 数量
MATCH (p:Pokemon)-[:HAS_TYPE]->(t:Type)
RETURN t.name, count(p) AS cnt ORDER BY cnt DESC

-- 威力最高的招式 Top 10
MATCH (m:Move)-[:HAS_TYPE]->(t:Type)
RETURN m.name, m.power, t.name ORDER BY m.power DESC LIMIT 10

-- 体重最大的 Pokemon Top 10
MATCH (p:Pokemon) RETURN p.name, p.weight ORDER BY p.weight DESC LIMIT 10
```

## 图谱 Schema
{schema}

## 示例
用户问："皮卡丘有什么属性？"
返回：MATCH (p:Pokemon {{name: "pikachu"}})-[:HAS_TYPE]->(t:Type) RETURN t.name

用户问："小火龙有什么特性？"
返回：MATCH (p:Pokemon {{name: "charmander"}})-[:HAS_ABILITY]->(a:Ability) RETURN a.name

用户问："喷火龙的体重是多少？"
返回：MATCH (p:Pokemon {{name: "charizard"}}) RETURN p.name, p.weight

用户问："火属性克制哪些属性？"
返回：MATCH (f:Type {{name: "fire"}})-[:DAMAGE_TO {{multiplier: 2.0}}]->(t:Type) RETURN t.name

用户问："什么属性克制水？"
返回：MATCH (f:Type)-[:DAMAGE_TO {{multiplier: 2.0}}]->(t:Type {{name: "water"}}) RETURN f.name

用户问："皮卡丘会什么招式？"
返回：MATCH (p:Pokemon {{name: "pikachu"}})-[:CAN_LEARN]->(m:Move) RETURN m.name LIMIT 10

用户问："哪些属性被火属性两倍克制？"
返回：MATCH (f:Type {{name: "fire"}})-[:DAMAGE_TO {{multiplier: 2.0}}]->(t:Type) RETURN t.name

用户问："十万伏特是什么属性的招式？"
返回：MATCH (m:Move {{name: "thunderbolt"}})-[:HAS_TYPE]->(t:Type) RETURN m.name, t.name

## 用户问题
{question}

请只返回 Cypher 查询语句，不要包含其他内容。
""".strip()


def generate_cypher(question: str) -> str:
    """根据问题生成 Cypher

    Args:
        question: 用户问题（自然语言）

    Returns:
        Cypher 查询语句

    Raises:
        ValueError: 生成的内容不是有效的 Cypher 语句
    """
    prompt = CYPHER_PROMPT.format(
        schema=get_schema(),
        question=question
    )
    cypher = call_llm(prompt, temperature=0.1)

    # 清理 markdown 标记
    cypher = cypher.strip()
    cypher = re.sub(r'^```(?:cypher)?\s*', '', cypher, flags=re.IGNORECASE)
    cypher = re.sub(r'```\s*$', '', cypher).strip()

    # 合并多行 Cypher（去掉空行，保留有效语句行）
    lines = [line.strip() for line in cypher.split('\n') if line.strip()]
    cypher = ' '.join(lines)

    if not cypher:
        raise ValueError("LLM 返回了空的 Cypher 语句")

    # 基本安全检查：必须是合法的 Cypher 开头
    valid_prefixes = ('MATCH', 'WITH', 'UNWIND', 'CALL', 'RETURN')
    if not cypher.upper().startswith(valid_prefixes):
        logger.warning(f"Generated non-Cypher content: {cypher[:100]}")
        raise ValueError(f"LLM 未返回有效的 Cypher 语句: {cypher[:200]}")

    logger.info(f"Generated Cypher: {cypher}")
    return cypher


if __name__ == "__main__":
    q = "皮卡丘有什么属性？"
    print(f"问题：{q}")
    print(f"生成 Cypher: {generate_cypher(q)}")
