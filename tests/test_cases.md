# 测试用例

## 实体查询类

| 编号 | 问题 | 预期 Cypher | 预期答案 |
|------|------|------------|---------|
| T1 | "皮卡丘是什么属性？" | `MATCH (p:Pokemon {name: "pikachu"})-[:HAS_TYPE]->(t:Type) RETURN t.name` | "皮卡丘是电属性宝可梦" |
| T2 | "小火龙有什么特性？" | `MATCH (p:Pokemon {name: "charmander"})-[:HAS_ABILITY]->(a:Ability) RETURN a.name` | 列出特性名称 |
| T3 | "喷火龙的体重是多少？" | `MATCH (p:Pokemon {name: "charizard"}) RETURN p.weight` | "喷火龙的体重是 90.5kg" |

## 属性克制类

| 编号 | 问题 | 预期 Cypher | 预期答案 |
|------|------|------------|---------|
| T4 | "火属性克制哪些属性？" | `MATCH (f:Type {name: "fire"})-[:EFFECTIVE_TO {multiplier: 2.0}]->(t:Type) RETURN t.name` | "火属性克制草、冰、虫、钢" |
| T5 | "哪些属性克制水？" | `MATCH (t:Type {name: "water"})<-[:EFFECTIVE_TO {multiplier: 2.0}]-(weak:Type) RETURN weak.name` | "电属性和草属性克制水" |

## 进化链类

| 编号 | 问题 | 预期 Cypher | 预期答案 |
|------|------|------------|---------|
| T6 | "妙蛙种子如何进化？" | `MATCH (p:Pokemon {name: "bulbasaur"})-[:EVOLVES_TO]->(next) RETURN next.name` | "妙蛙种子进化成妙蛙草" |

## 验证方式

### 手动测试

1. 调用 `/api/query` 执行预期 Cypher，验证结果正确
2. 调用 `/api/chat` 输入问题，验证回答符合预期

### 通过标准

- 至少 8/10 个用例通过
- 答案语义正确即可，不要求字句完全一致
