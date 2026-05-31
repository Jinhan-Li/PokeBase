## 2. 节点（Node）

### 2.1 Pokemon

| 属性 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | Integer | 全国图鉴编号 | `1` |
| `name` | String | 英文名（小写） | `"bulbasaur"` |
| `height` | Integer | 身高（分米） | `7` |
| `weight` | Integer | 体重（百克） | `69` |
| `base_experience` | Integer | 基础经验值 | `64` |
| `hp` | Integer | 种族值：HP | `45` |
| `attack` | Integer | 种族值：攻击 | `49` |
| `defense` | Integer | 种族值：防御 | `49` |
| `special_attack` | Integer | 种族值：特攻 | `65` |
| `special_defense` | Integer | 种族值：特防 | `65` |
| `speed` | Integer | 种族值：速度 | `45` |



### 2.2 Type

| 属性 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | Integer | 属性编号 | `13` |
| `name` | String | 英文名（小写） | `"electric"` |

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

### 2.4 Move

| 属性 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | Integer | 招式编号 | `85` |
| `name` | String | 英文名（小写） | `"thunderbolt"` |
| `power` | Integer | 威力 | `90` |
| `accuracy` | Integer | 命中率（%） | `100` |
| `pp` | Integer | 使用次数 | `15` |
| `priority` | Integer | 优先度 | `0` |
| `damage_class` | String | 物理/特殊/变化 | `"special"` |

---

## 3. 关系（Relationship）

### 3.1 HAS_TYPE

```
(Pokemon)-[:HAS_TYPE]->(Type)
```

- **说明**：每个 Pokemon 有 1~2 个属性
- **属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `slot` | Integer | 属性槽位（1：主要属性，2：次要属性） |

```cypher
-- 查看皮卡丘的属性及槽位
MATCH (p:Pokemon {name: "pikachu"})-[r:HAS_TYPE]->(t:Type)
RETURN p.name, t.name, r.slot
-- 结果: pikachu, electric, 1
```

### 3.2 HAS_ABILITY

```
(Pokemon)-[:HAS_ABILITY]->(Ability)
```

- **说明**：每个 Pokemon 有 1~3 个特性
- **属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `is_hidden` | Boolean | 是否为隐藏特性（梦特） |
| `slot` | Integer | 特性槽位（通常 1或2 为普通特性，3 为隐藏特性） |

```cypher
-- 查看小火龙的隐藏特性
MATCH (p:Pokemon {name: "charmander"})-[r:HAS_ABILITY {is_hidden: true}]->(a:Ability)
RETURN p.name, a.name
-- 结果: charmander → solar-power
```

### 3.3 CAN_LEARN

```
(Pokemon)-[:CAN_LEARN]->(Move)
```

- **说明**：Pokemon 可学会的招式
- **属性**：由于不同版本和学习方式的存在，这些属性是以列表形式并行记录的。

| 属性 | 类型 | 说明 |
|------|------|------|
| `versions` | List[String] | 可学习该招式的游戏版本组（如 "red-blue", "sword-shield" 等） |
| `methods` | List[String] | 学习方式（如 "level-up" 升级, "machine" 学习机, "egg" 遗传等） |
| `levels` | List[Integer] | 习得等级（若通过升级学习则为具体等级，否则通常为 0） |

```cypher
-- 查询能通过升级（level-up）在 50 级之后学会特定招式的宝可梦
MATCH (p:Pokemon)-[r:CAN_LEARN]->(m:Move)
WHERE 'level-up' IN r.methods AND ANY(lvl IN r.levels WHERE lvl >= 50)
RETURN p.name, m.name LIMIT 10
```

### 3.4 EVOLVES_TO & EVOLVES_FROM

```
(Pokemon)-[:EVOLVES_TO]->(Pokemon)
(Pokemon)-[:EVOLVES_FROM]->(Pokemon)
```

- **说明**：宝可梦的进化关系，为双向连通。
- **属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `min_level` | Integer | 进化的最低等级要求（非等级进化则为 null） |
| `item` | String | 进化所需物品（如 "fire-stone" 火之石，非物品进化则为 null） |
| `details` | String | 变长 JSON 字符串，记录其余所有复杂的进化要求（如 "min_happiness": 220 亲密度、"time_of_day": "night" 特定时间、"location": "mt-coronet" 特定地点等，由于情况复杂，统一存作序列化 JSON 文本，可通过 CONTAINS 匹配） |

```cypher
-- 大器晚成宝可梦（50 级后进化）
MATCH (from:Pokemon)-[r:EVOLVES_TO]->(to:Pokemon)
WHERE r.min_level >= 50
RETURN from.name, to.name, r.min_level

-- 查看必须在特定地点（如 mt-coronet 殿元山）进化的宝可梦
MATCH (from:Pokemon)-[r:EVOLVES_TO]->(to:Pokemon) 
WHERE r.details CONTAINS '"location": "mt-coronet"' 
RETURN from.name, to.name
```

### 3.5 HAS_TYPE（Move → Type）

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
```

---



