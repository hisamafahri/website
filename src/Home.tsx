const HomePage = () => {
  return (
    <main className="bg-neutral-50 h-full min-h-screen">
      <section className="w-full max-w-xl mx-auto">
        <div className="py-8">
          <img
            src="https://files.hisam.dev/pictures/pp_01.jpeg"
            className="size-8 rounded"
          />
        </div>
        <h1 className="text-neutral-500 text-sm">Halo!</h1>
        <p className="text-neutral-800 text-sm">
          Hisam, here! Welcome to my spaces 👋
        </p>

        <h2 className="text-neutral-500 text-sm mt-8">Currently</h2>
        <div className="flex items-center justify-between mt-1">
          <a
            href="https://buybuy.id"
            className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4 text-sm"
            target="_blank"
          >
            Buybuy
          </a>
          <p className="text-neutral-500 text-sm text-right">
            Startup (w/ my friend)
          </p>
        </div>
        <div className="flex items-center justify-between mt-2">
          <a
            href="https://bunayaya.id"
            className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4 text-sm"
            target="_blank"
          >
            BUNAYAYA
          </a>
          <p className="text-neutral-500 text-sm text-right">
            Baby clothing store (w/ my wife)
          </p>
        </div>
        <div className="flex items-center justify-between mt-2">
          <a
            href="https://x.com/bytehaf"
            className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4 text-sm"
            target="_blank"
          >
            Bytehaf
          </a>
          <p className="text-neutral-500 text-sm text-right">
            Live-streaming alias
          </p>
        </div>
        <div className="flex items-center justify-between mt-2">
          <a
            href="https://cakeauth.com"
            className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4 text-sm"
            target="_blank"
          >
            Cakeauth
          </a>
          <p className="text-neutral-500 text-sm text-right">
            Another startup (hiatus)
          </p>
        </div>
        <div className="flex items-center justify-between mt-2">
          <a
            href="https://www.persolapac.com/"
            className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4 text-sm"
            target="_blank"
          >
            PERSOL
          </a>
          <p className="text-neutral-500 text-sm text-right">Regular 9-5 job</p>
        </div>

        <h2 className="text-neutral-500 text-sm mt-8">Connect</h2>
        <p className="text-neutral-800 text-sm">
          Feel free to reach me on{" "}
          <a
            href="mailto:iam@hisamafahri.com"
            className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4"
          >
            email
          </a>{" "}
          (
          <a
            href="/pgp.txt"
            className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4"
          >
            pgp
          </a>
          ),{" "}
          <a
            href="https://x.com/hisamafahri"
            target="_blank"
            className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4"
          >
            X
          </a>
          ,{" "}
          <a
            href="https://github.com/hisamafahri"
            target="_blank"
            className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4"
          >
            GitHub
          </a>
          , or even have a{" "}
          <a
            href="https://cal.com/hisam"
            target="_blank"
            className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4"
          >
            chat with me
          </a>
          .
        </p>

        <h2 className="text-neutral-500 text-sm mt-8">Journals</h2>
        <p className="text-neutral-800 text-sm">Coming soon...</p>
      </section>
    </main>
  );
};

export default HomePage;
