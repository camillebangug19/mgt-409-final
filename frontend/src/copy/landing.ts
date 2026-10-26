/**
 * Landing page copy, used exactly as written in REQUIREMENTS.md 18.2.
 * Kept in one file so the wording can be checked against the spec at a glance.
 */
export const LANDING = {
  eyebrow: 'Free · No sign-up · About 3 minutes',
  headline: "You've got this. Let's get your family ready together.",
  subhead:
    "Answer a few easy questions and we'll show you how ready your household already is, plus three small steps to feel even more prepared.",
  button: "Let's get started →",
  underButton: 'No account, no judgment. Every family starts somewhere.',
  tiles: [
    { big: '3 easy minutes', cap: 'just tap or type' },
    { big: 'Your score out of 10', cap: 'made for your family' },
    { big: '3 small wins', cap: 'free ones first' },
  ],
  howItWorksTitle: 'How it works',
  howItWorks: [
    {
      lead: 'Tell us about your crew.',
      rest: 'Little ones, grandparents, anyone who might need an extra hand, and your pets too.',
    },
    {
      lead: "See how far you've already come.",
      rest: "Your score is built from Ready.gov, CDC and Red Cross checklists. Anything that doesn't apply to your home doesn't count against you.",
    },
    {
      lead: 'Take it one step at a time.',
      rest: 'Three simple steps, each worth points. Check one off and watch your go-bag fill up.',
    },
  ],
  closing:
    "Being prepared isn't about being perfect. It's about taking the next small step, and we'll be with you for each one.",
  footer:
    'Not medical advice. Ask your doctor or pharmacist about medications and medical equipment.',
} as const
