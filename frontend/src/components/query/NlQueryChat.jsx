import { useState } from "react";
import QueryResult from "./QueryResult";

export default function NlQueryChat({ onQuery }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [asking, setAsking] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || asking) return;

    setAsking(true);
    setQuestion("");

    try {
      const body = await onQuery(trimmed);
      setMessages((prev) => [
        ...prev,
        {
          question: trimmed,
          answer: body.answer,
          resultType: body.result_type,
          generatedCode: body.generated_code,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { question: trimmed, error: err.message },
      ]);
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="flex flex-col rounded-xl border border-gray-200 bg-white">
      <div className="border-b border-gray-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-gray-800">NL-Query</h2>
        <p className="text-xs text-gray-500">
          Ask a question in plain English — answered by running pandas
          code against the current (cleaned) dataset.
        </p>
      </div>

      <div className="flex max-h-96 flex-col gap-4 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400">
            e.g. "What's the average fare by class?"
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className="flex flex-col gap-1">
            <div className="self-end rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-800">
              {m.question}
            </div>
            {m.error ? (
              <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                {m.error}
              </div>
            ) : (
              <QueryResult
                resultType={m.resultType}
                answer={m.answer}
                generatedCode={m.generatedCode}
              />
            )}
          </div>
        ))}
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-gray-200 px-6 py-4"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about this dataset…"
          disabled={asking}
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={asking || !question.trim()}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
        >
          {asking ? "Thinking…" : "Ask"}
        </button>
      </form>
    </div>
  );
}