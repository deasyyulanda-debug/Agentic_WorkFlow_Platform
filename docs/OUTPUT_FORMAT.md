# Output Format Update

## Overview

The workflow execution output format has been enhanced to provide both **human-readable formatted output** and **raw structured data** for programmatic access.

## New Response Structure

When you execute a workflow, the response now contains:

```json
{
  "run": { ... },  // Run metadata
  "output": {
    "formatted": "...",  // Human-readable text format
    "raw": {             // Original structured data
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

## Formatted Output Example

The `formatted` field provides a clean, readable output:

```
1. Define Scope & Data Preparation

   • Clearly define the target domain, use case, and desired accuracy/performance.
   • Gather, clean, and prepare your knowledge base (documents, website content, databases, etc.).
   • Consider data augmentation techniques to improve the quality and coverage of your data.
   • This stage also includes choosing the appropriate data format and storage solution.

2. Build Indexing & Retrieval

   • Implement the indexing strategy (chunking, metadata extraction).
   • Select a suitable embedding model (e.g., OpenAI's embeddings, Sentence Transformers).
   • Choose a vector database (e.g., Chroma, Pinecone, FAISS) for similarity search and retrieval.
   • Optimize retrieval strategies for speed and accuracy (e.g., hybrid search, re-ranking).

3. Develop & Test the Generation Pipeline

   • Select a suitable Large Language Model (LLM) (e.g., GPT-3.5/4, Llama 2, Gemini).
   • Design the prompt engineering strategy to integrate retrieved context with user queries.
   • Develop the generation pipeline with proper formatting and information flow.
   • Implement evaluation metrics (e.g., ROUGE, BLEU, context relevance, factuality).
   • Iterate based on evaluation results.

4. Implement Infrastructure & Scalability

   • Design system architecture: API endpoints, caching, monitoring tools.
   • Choose infrastructure (cloud providers, serverless functions) for expected traffic/load.
   • Implement scalability (e.g., horizontal scaling, distributed processing).
   • Consider cost implications of infrastructure choices.

5. Deploy, Monitor & Maintain

   • Deploy the RAG system to a production environment.
   • Set up monitoring for latency, error rate, and cost.
   • Establish a feedback loop for user input and continuous improvement.
   • Monitor the knowledge base for outdated info and update as needed.
   • Retrain embedding models and fine-tune LLMs regularly.
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

## Metrics Breakdown

The execution summary at the bottom includes:

| Metric | Description |
|--------|-------------|
| **Input Tokens** | Approximate tokens used for input prompts (~40% of total) |
| **Output Tokens** | Approximate tokens generated as output (~60% of total) |
| **Total Tokens** | Total tokens consumed during execution |
| **Provider** | AI provider used (OpenAI, Anthropic, Gemini, DeepSeek) |
| **Iterations** | Number of workflow iterations executed |
| **Steps Executed** | Number of steps completed |
| **Completion Time** | Total execution duration in seconds |

## Frontend Integration

### Displaying Formatted Output

To display the formatted output in your frontend:

```typescript
// In your React component
const { data: result } = useQuery(['run', runId], () => api.getRun(runId));

// Display the formatted output
<pre className="whitespace-pre-wrap font-mono text-sm">
  {result?.output?.formatted}
</pre>
```

### Accessing Raw Data

For programmatic access or custom formatting:

```typescript
// Access raw structured data
const rawOutput = result?.output?.raw;
const finalStepOutput = rawOutput?.final;
const allSteps = rawOutput?.all_steps;

// Custom processing
allSteps?.forEach((step, index) => {
  console.log(`Step ${index + 1}:`, step.output);
  console.log(`Tokens used:`, step.tokens);
});
```

## API Endpoints Affected

The new format applies to these endpoints:

1. **POST /api/v1/runs/execute-async**
   - Returns run metadata immediately
   - Formatted output available when run completes

2. **POST /api/v1/runs/{run_id}/execute**
   - Returns formatted output directly in response

3. **GET /api/v1/runs/{run_id}**
   - Returns formatted output if execution is complete

## Backward Compatibility

- The `raw` field contains the original data structure
- Existing integrations can continue using `output.raw.final` and `output.raw.all_steps`
- New integrations should use `output.formatted` for display purposes

## Customizing Output Format

The output formatter is located at:
```
apps/api/src/engine/output_formatter.py
```

You can customize:
- Section formatting
- Bullet point styles
- Metrics display
- Token calculation ratios

## Token Estimation

Token counts are split approximately:
- **40%** attributed to input (prompts, context)
- **60%** attributed to output (generated responses)

Note: These are estimates. For exact counts, refer to the provider's API response when available.
