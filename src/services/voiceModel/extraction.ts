/**
 * Parses the fenced ```json block that the Local-mode system prompts
 * (see prompts.ts) instruct Gemma to emit after its natural-language reply.
 * Tolerates a missing or malformed block — falls back to "no structured
 * data extracted" the same way the existing `hasData()` check already gates
 * `propose_registration_data` in registration/page.tsx.
 */
export function parseStructuredReply<T = Record<string, unknown>>(
  fullText: string
): { reply: string; extracted: T | null } {
  const fenceMatch = fullText.match(/```json\s*([\s\S]*?)\s*```/i);

  if (!fenceMatch) {
    return { reply: fullText.trim(), extracted: null };
  }

  const reply = (fullText.slice(0, fenceMatch.index) + fullText.slice(fenceMatch.index! + fenceMatch[0].length))
    .trim();

  try {
    const parsed = JSON.parse(fenceMatch[1]);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return { reply, extracted: parsed as T };
    }
    return { reply, extracted: null };
  } catch {
    // Malformed JSON from the model — surface the reply text, no structured data.
    return { reply, extracted: null };
  }
}
