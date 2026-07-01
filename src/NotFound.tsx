import { Link } from "react-router-dom";

const NotFoundPage = () => {
  return (
    <main className="bg-neutral-50 h-full min-h-screen pb-18 px-4">
      <section className="w-full max-w-xl mx-auto">
        <div className="py-8">
          <img
            src="https://files.hisam.dev/pictures/pp_01.jpeg"
            className="size-8 rounded"
          />
        </div>
        <h1 className="text-neutral-500 text-sm">404</h1>
        <p className="text-neutral-800 text-sm">Page not found.</p>
        <p className="text-neutral-800 text-sm mt-2">
          <Link
            to="/"
            className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4"
          >
            Go back home
          </Link>
        </p>
      </section>
    </main>
  );
};

export default NotFoundPage;
