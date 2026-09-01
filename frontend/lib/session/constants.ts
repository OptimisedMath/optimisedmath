/** Preferred chapter when resuming an arena session from stored credentials. */
export const PREFERRED_CHAPTER_ID = 10;

/** Fallback label when the backend omits the current Topic name. */
export const MISSING_TOPIC_NAME = 'Aktualny temat';

export const SESSION_STORAGE_KEYS = ['username', 'session_id'] as const;

/**
 * Joins/splits an ordering step's submitted order on the wire — `user_input`
 * stays a plain string (matching the typed-answer wire shape), carrying the
 * ordered items joined by this separator. Mirrors
 * `backend/step_grading.ORDERING_ANSWER_SEPARATOR`.
 */
export const DECONSTRUCTION_ORDERING_SEPARATOR = '|';
