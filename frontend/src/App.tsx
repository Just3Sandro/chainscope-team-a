import { useQuery } from '@tanstack/react-query'
import { Link, Route, Routes } from 'react-router-dom'
import { getHealth } from './api/client'

function Home() {
  const health = useQuery({ queryKey: ['health'], queryFn: getHealth, retry: false })
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-semibold tracking-tight">ChainScope</h1>
      <p className="mt-3 text-slate-600">Espace de suivi des audits de sécurité.</p>
      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6" aria-label="État du service">
        <h2 className="text-lg font-medium">Connexion à l’API</h2>
        {health.isPending && <p role="status">Vérification en cours…</p>}
        {health.isError && <p role="alert">L’API est indisponible. Veuillez réessayer.</p>}
        {health.isSuccess && <p role="status">API opérationnelle.</p>}
      </section>
    </main>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="*" element={
        <main className="mx-auto max-w-3xl px-6 py-16">
          <h1 className="text-3xl font-semibold">Page introuvable</h1>
          <Link className="mt-6 inline-block underline" to="/">Retour à l’accueil</Link>
        </main>
      } />
    </Routes>
  )
}
