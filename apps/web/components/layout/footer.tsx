export function Footer() {
  return (
    <footer className="border-t py-6 md:py-0">
      <div className="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
        <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
          Built with FastAPI & Next.js. Powered by AI Providers.
        </p>
        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
          <span>v1.0.0</span>
          <span>•</span>
          <a href="/docs" className="hover:underline">
            API Docs
          </a>
        </div>
      </div>
    </footer>
  );
}
