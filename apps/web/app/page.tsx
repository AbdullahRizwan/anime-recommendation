import { PreferencesForm } from "../components/PreferencesForm";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="mx-auto max-w-2xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Anime Triage</h1>
          <p className="mt-2 text-gray-500">
            Tell us what you like and we&apos;ll rank the best anime this season.
          </p>
        </div>
        <PreferencesForm />
      </div>
    </main>
  );
}
