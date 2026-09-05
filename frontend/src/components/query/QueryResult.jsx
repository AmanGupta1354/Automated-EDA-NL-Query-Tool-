function TableAnswer({ answer }) {
  // The agent's "table" answers arrive as a preformatted, whitespace-
  // aligned string (a stringified pandas Series/DataFrame), not
  // structured JSON — see nl_query_agent.py's classify_result_type
  // caveat. Rendered in <pre> to preserve alignment.
  return (
    <pre className="overflow-x-auto rounded-lg bg-gray-50 p-3 text-xs text-gray-800">
      {answer}
    </pre>
  );
}

function NumberAnswer({ answer }) {
  return (
    <div className="rounded-lg bg-indigo-50 px-4 py-3 text-xl font-semibold text-indigo-700">
      {answer}
    </div>
  );
}

function TextAnswer({ answer }) {
  return <p className="text-sm text-gray-800">{answer}</p>;
}

export default function QueryResult({ resultType, answer, generatedCode }) {
  return (
    <div className="flex flex-col gap-2">
      {resultType === "number" && <NumberAnswer answer={answer} />}
      {resultType === "table" && <TableAnswer answer={answer} />}
      {resultType === "text" && <TextAnswer answer={answer} />}

      {generatedCode && (
        <details className="text-xs text-gray-400">
          <summary className="cursor-pointer select-none hover:text-gray-600">
            Show generated code
          </summary>
          <pre className="mt-1 overflow-x-auto rounded bg-gray-900 p-2 text-gray-100">
            {generatedCode}
          </pre>
        </details>
      )}
    </div>
  );
}