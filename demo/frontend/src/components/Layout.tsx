// Layout wrapper — sticky header, max-width content column, slim footer.
// Footer lives inside <main> so it sits flush with the content; no extra page
// chrome to wrestle with at small widths.

import type { ReactNode } from 'react';
import Header from './Header';
import Footer from './Footer';

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => (
  <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 antialiased">
    <Header />
    <main className="flex-grow max-w-6xl w-full mx-auto px-6 py-8">
      {children}
      <Footer />
    </main>
  </div>
);

export default Layout;
