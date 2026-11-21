// What a person reads for a refusal of a project route. Never repeats text from the API or the input,
// and a hidden project reads the same as a missing one (AC-27).
const MESSAGES: Record<string, string> = {
  forbidden: "You may not do this.",
  member_not_eligible: "That person cannot be a member: they need an active account, or they are not a member.",
  invalid_project_name: "The name must have 1 to 100 characters.",
  invalid_request: "The request was not valid.",
  project_not_found: "This project is not available.",
};

export function projectRefusalMessage(code: string): string {
  return Object.hasOwn(MESSAGES, code) ? MESSAGES[code] : "Something went wrong. Try again.";
}
