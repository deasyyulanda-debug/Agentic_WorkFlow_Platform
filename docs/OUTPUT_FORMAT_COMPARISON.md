# Output Format Comparison

## Before (Old Format)

```json
{
  "final": {
    "type": "prompt",
    "output": "Okay, I need the output of Step 1...",
    "tokens": 81,
    "variable": "step_1_output"
  },
  "all_steps": [
    {
      "type": "prompt",
      "output": "*   **1. Define Scope & Data Preparation:**  Clearly define...",
      "tokens": 533,
      "variable": "step_0_output"
    },
    {
      "type": "prompt",
      "output": "Okay, I need the output of Step 1...",
      "tokens": 81,
      "variable": "step_1_output"
    }
  ],
  "_metrics": {
    "total_tokens": 614,
    "duration_seconds": 6.911963,
    "steps_executed": 2,
    "iterations": 2,
    "provider": "gemini"
  }
}
```

### Issues with Old Format:
- ❌ Hard to read in raw JSON
- ❌ Markdown formatting embedded in strings
- ❌ No clear separation of content and metrics
- ❌ Requires manual parsing for display

---

## After (New Format)

```json
{
  "run": { "id": "...", "status": "completed", ... },
  "output": {
    "formatted": "1. Define Scope & Data Preparation\n\n   • Clearly define...",
    "raw": {
      "final": { ... },
      "all_steps": [ ... ]
    }
  },
  "metrics": {
    "total_tokens": 614,
    "duration_seconds": 6.91,
    "steps_executed": 2,
    "iterations": 2,
    "provider": "gemini"
  }
}
```

### Display Output (formatted field):

```
1. Define Scope & Data Preparation

   • Clearly define the target domain, use case, and desired accuracy/performance.
   • Gather, clean, and prepare your knowledge base (documents, website content, databases, etc.).
   • Consider data augmentation techniques to improve the quality and coverage of your data.
   • This stage also includes choosing the appropriate data format and storage solution.

2. Build Indexing & Retrieval

   • Implement the indexing strategy (chunking, metadata extraction).
   • Select a suitable embedding model (e.g., OpenAI's embeddings, Sentence Transformers).
   • Choose a vector database (e.g., Chroma, Pinecone, FAISS).
   • Optimize retrieval strategies for speed and accuracy.

3. Develop & Test the Generation Pipeline

   • Select a suitable Large Language Model (LLM).
   • Design the prompt engineering strategy.
   • Develop the generation pipeline with proper formatting.
   • Implement evaluation metrics (ROUGE, BLEU, context relevance).
   • Iterate based on evaluation results.

4. Implement Infrastructure & Scalability

   • Design system architecture: API endpoints, caching, monitoring tools.
   • Choose infrastructure for expected traffic/load.
   • Implement scalability strategies.
   • Consider cost implications.

5. Deploy, Monitor & Maintain

   • Deploy the RAG system to production.
   • Set up monitoring for latency, error rate, and cost.
   • Establish a feedback loop for continuous improvement.
   • Monitor and update the knowledge base regularly.
   • Retrain embedding models and fine-tune LLMs.
   • Implement robust security measures.

────────────────────────────────────────────────────────────

📊 Execution Summary

   • Input Tokens:        245
   • Output Tokens:       369
   • Total Tokens:        614
   • Provider:            Gemini
   • Iterations:          2
   • Steps Executed:      2
   • Completion Time:     6.91 seconds

────────────────────────────────────────────────────────────
```

### Benefits of New Format:
- ✅ **Human-readable** - Clean, formatted text ready for display
- ✅ **Structured metrics** - Clear summary at the bottom
- ✅ **Token breakdown** - Input/output token estimates
- ✅ **Backward compatible** - Raw data still available
- ✅ **Frontend friendly** - Just display the `formatted` field
- ✅ **Professional appearance** - Proper formatting with bullets and sections

---

## Frontend Display Examples

### Simple Display
```typescript
<pre className="whitespace-pre-wrap font-mono text-sm p-4 bg-gray-50 rounded">
  {result.output.formatted}
</pre>
```

### Styled Display
```typescript
<div className="prose prose-sm max-w-none">
  {result.output.formatted.split('\n').map((line, i) => (
    <div key={i} className={line.startsWith('   •') ? 'ml-6' : ''}>
      {line}
    </div>
  ))}
</div>
```

### With Syntax Highlighting
```typescript
import ReactMarkdown from 'react-markdown';

<div className="bg-white rounded-lg p-6 shadow">
  <ReactMarkdown className="prose">
    {result.output.formatted}
  </ReactMarkdown>
</div>
```
