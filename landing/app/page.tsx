import Image from 'next/image';
import PhotoStory from './photo-story';

const Arrow = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>;
const Flower = ({ className = '' }: { className?: string }) => <svg className={className} viewBox="0 0 100 100" aria-hidden="true"><path d="M50 28C27-7 4 20 28 43-12 42-4 78 32 66 18 103 53 110 60 73 82 107 110 81 76 60 114 48 93 17 65 37 74-2 38-9 50 28Z" fill="currentColor"/><circle cx="51" cy="51" r="10" fill="var(--paper)"/></svg>;

export default function Home() {
  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header wrap">
      <a href="#" className="wordmark" aria-label="Motif Moments home"><Image className="brand-logo" src="/images/mm-logo-sm.png" alt="" width={40} height={40} sizes="40px"/>Motif Moments</a>
      <nav aria-label="Main navigation"><a href="#experience">The experience</a><a href="#questions">Good to know</a><a className="nav-cta" href="#frames">Find your frame <Arrow/></a></nav>
    </header>
    <main id="main">
      <section className="hero wrap" aria-labelledby="hero-title">
        <div className="hero-copy">
          <h1 id="hero-title">Make it{' '}<br/>a motif.{' '}<br/><span className="memory-line">Keep the{' '}<br/>memory.<svg viewBox="0 0 400 24" preserveAspectRatio="none" aria-hidden="true"><path d="M4 15 Q180 0 394 14" fill="none" stroke="currentColor" strokeWidth="10"/></svg></span></h1>
          <p>Your people. Your poses. Your little keepsake.<br className="desktop-break"/> A Korean-inspired self-photo booth for moments worth holding on to.</p>
          <a className="button" href="#frames">Explore the frames <Arrow/></a>
          <span className="hero-footnote">Come as you are. Leave with a memory.</span>
        </div>
        <div className="hero-art">
          <Image id="hero-image" src="/images/hero.webp" alt="Sample studio portraits of two friends, arranged with Motif Moments photo strips and a mint frame" width={1200} height={1100} sizes="(max-width: 700px) 100vw, 58vw" loading="eager" fetchPriority="high" quality={75}/>
          <span className="hero-sticker">a little<br/>moment,<br/><strong>all yours.</strong></span>
          <Flower className="hero-flower"/>
          <span className="photo-note">Good company. Great outtakes.</span>
          <span className="sample-caption">Illustrative AI-generated sample photos</span>
        </div>
        <a className="scroll-note" href="#experience"><span>Scroll to make a memory</span><svg width="18" height="22" viewBox="0 0 18 22" fill="none" aria-hidden="true"><path d="M9 1v18m-6-6 6 6 6-6" stroke="currentColor" strokeWidth="1.5"/></svg></a>
      </section>
      <section className="interlude" aria-label="Made for your moments"><div className="wrap"><span>A little pause.</span><Flower/><span>A very good memory.</span><Flower/><span>Made to keep.</span></div></section>
      <PhotoStory/>
      <section className="moments wrap" aria-labelledby="moments-title">
        <div className="moments-intro"><h2 id="moments-title">No occasion<br/>needed.</h2><p>The catch-up. The date. The “just because.”<br/>Sometimes being together is the whole occasion.</p></div>
        <div className="moment-photos">
          {[{ n: 4, label: 'Your favourite people.', alt: 'Two friends hugging and laughing' }, { n: 6, label: 'Your kind of love.', alt: 'An adult couple making a heart together' }, { n: 7, label: 'Your main-character moment.', alt: 'A woman posing with a peace sign' }].map(item => <figure key={item.n}><Image src={`/images/portrait-${item.n}.webp`} alt={`Illustrative sample: ${item.alt}`} width={640} height={480} sizes="(max-width: 700px) 85vw, 30vw"/><figcaption>{item.label}</figcaption></figure>)}
        </div>
      </section>
      <section id="questions" className="faq wrap" aria-labelledby="faq-title">
        <div><h2 id="faq-title">A few things<br/>before you pose.</h2><p>Less wondering. More memory-making.</p></div>
        <div className="faq-list">
          {[
            ['How does a session work?', 'Pay at the booth, choose and confirm your frame, then follow the on-screen countdowns. The booth takes your full photo sequence and puts your finished collage together for you.'],
            ['What comes with my session?', 'Your selected 4-, 6-, or 8-photo layout, one print, and a QR code to download your finished collage. Four Strip ×2 places two matching strips on the same print.'],
            ['Can I take the photos again?', 'One complete retake is included before you print. A retake replaces the entire first sequence; only the new result can be printed. Printing your first result closes the retake option.'],
            ['How do I save my digital copy?', 'Scan the QR code at the booth to download your finished collage directly. No account needed. Download it within seven days, before the stored result is deleted.'],
            ['Do I need to know how to pose?', 'Not at all. Follow the on-screen countdown, look at the camera, and make it yours. A smile, a peace sign, or your very best silly face all belong here.'],
          ].map(([question, answer]) => <details key={question}><summary>{question}<span aria-hidden="true" className="plus"/></summary><p>{answer}</p></details>)}
        </div>
      </section>
      <section className="closing"><Image className="closing-logo" src="/images/mm-logo-xl.png" alt="" width={160} height={160} sizes="(max-width: 700px) 88px, 116px"/><h2>Your next little<br/>memory starts here.</h2><a className="button" href="#frames">Find your favourite frame <Arrow/></a><p>Make it a motif. Keep the memory.</p></section>
    </main>
    <footer className="site-footer wrap"><a href="#" className="wordmark" aria-label="Motif Moments home"><Image className="brand-logo" src="/images/mm-logo-sm.png" alt="" width={40} height={40} sizes="40px"/>Motif Moments</a><span>Little moments. Lasting keepsakes.</span><a href="#main">Back to top <span aria-hidden="true">↑</span></a></footer>
  </>;
}
