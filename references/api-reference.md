# Smart Code Library — API Reference

Base URL (local development): `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

---

## POST `/seed`

Index reference content into the vector memory store.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Text to embed and store |
| `category` | string | Yes | Logical grouping (e.g. `"Authentication"`, `"Self-Healing Patch"`) |
| `language` | string | No | Programming language tag (default: `"All"`) |

### Response

```json
{
  "message": "Data indexed accurately."
}
```

### Example

```bash
curl -X POST http://localhost:8000/seed \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Use bcrypt with a cost factor of 12 for password hashing in Python.",
    "category": "Security",
    "language": "Python"
  }'
```

---

## POST `/query`

Retrieve semantically similar context and generate an LLM-powered answer.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Natural-language question or code-related prompt |

### Response

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | LLM-generated answer using retrieved context |
| `referenced_context` | string | Concatenated top-k similarity matches (default k=3) |

### Example

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I hash passwords securely in Python?"
  }'
```

### Example Response

```json
{
  "response": "Use bcrypt with a cost factor of 12...",
  "referenced_context": "[Security]: Use bcrypt with a cost factor of 12 for password hashing in Python."
}
```

---

## POST `/execute-heal`

Execute Python code in the sandbox. On failure, automatically attempts LLM-driven fixes up to 3 times.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Python source code to execute and optionally heal |

### Response

```json
{
  "report": {
    "status": "Healed",
    "code": "...",
    "attempts": 2
  }
}
```

### Success Report Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"Healed"` when execution succeeds |
| `code` | string | Final (possibly fixed) source code |
| `attempts` | integer | Number of execution attempts until success |

### Failure Report Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"Failed"` |
| `code` | string | Original broken code |
| `error` | string | Last traceback from execution |

### Example — Broken Code

```bash
curl -X POST http://localhost:8000/execute-heal \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(greeting)"
  }'
```

### Example — Healed Response

```json
{
  "report": {
    "status": "Healed",
    "code": "greeting = \"Hello, World!\"\nprint(greeting)",
    "attempts": 1
  }
}
```

---

## Error Handling

- Invalid JSON or missing required fields → `422 Unprocessable Entity` (Pydantic validation)
- Server misconfiguration (e.g. Ollama not running or model not pulled) → `503` or degraded `/health`

## Models (Pydantic)

```python
class QueryRequest(BaseModel):
    query: str

class SeedingRequest(BaseModel):
    content: str
    category: str
    language: str

class CodeRunRequest(BaseModel):
    code: str
```