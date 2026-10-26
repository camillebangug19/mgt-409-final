import { Sunny } from './Sunny'

/**
 * The app's name, on every screen.
 *
 * Added after the first real user session: the tester pointed out that
 * "the name isn't anywhere on the page", which was true — ReadyHome only
 * appeared in the browser tab title.
 */
export function BrandBar() {
  return (
    <header className="brandbar">
      <Sunny mood="hi" size={30} />
      <span className="brandname">ReadyHome</span>
      <span className="brandtag">household readiness, one step at a time</span>
    </header>
  )
}
