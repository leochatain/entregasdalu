import { useConfig, useDevLogin } from '../api/hooks'
import CtaButton from '../components/CtaButton'
import Eyebrow from '../components/Eyebrow'

/**
 * Sign-in gate. Real Google OAuth is a full-page redirect to allauth (not fetch).
 * In DEBUG the backend exposes a dev-login bypass; `config.devLogin` reveals it.
 */
export default function SignIn() {
  const { data: config } = useConfig()
  const devLogin = useDevLogin()

  return (
    <main className="mx-auto flex min-h-screen max-w-[680px] flex-col justify-center gap-9 px-6 py-16">
      <Eyebrow className="tracking-[.34em]">entregas da lu</Eyebrow>

      <h1 className="text-hero text-ink font-serif leading-[1.05] font-light">
        Oi, boa noite, será que vai ter{' '}
        <em className="text-accent italic">entrega</em> da Lu hoje?
      </h1>

      <div className="border-line-warm flex flex-col items-start gap-5 border-t pt-8">
        <a
          href="/accounts/google/login/"
          className="bg-ink text-bg focus-visible:outline-accent inline-flex cursor-pointer items-center gap-3 rounded-[3px] px-7 py-3.5 font-serif text-[18px] no-underline transition duration-200 hover:-translate-y-0.5 hover:brightness-[1.15] focus-visible:outline-2 focus-visible:outline-offset-2"
        >
          <span
            aria-hidden
            className="bg-bg text-ink inline-flex h-[22px] w-[22px] items-center justify-center rounded-full font-mono text-[13px] font-bold"
          >
            G
          </span>
          Entrar com Google
        </a>

        <p className="text-muted-2 font-serif text-[15px] italic">
          só a Lu entra aqui. (oi, Lu.)
        </p>

        {config?.devLogin && (
          <CtaButton
            onClick={() => devLogin.mutate()}
            disabled={devLogin.isPending}
            className="text-muted border-line border bg-transparent px-5 py-2 text-[14px] hover:brightness-100"
          >
            entrar (dev)
          </CtaButton>
        )}
      </div>
    </main>
  )
}
