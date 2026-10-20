// components/layout/PageLayout.jsx
// Every farmer/expert/admin page wraps itself in this.
// Usage: <PageLayout title="Dashboard">...</PageLayout>
import Sidebar from './Sidebar';
import Navbar  from './Navbar';

const PageLayout = ({ title, children }) => (
  <div className="flex min-h-screen bg-[#0a150a]">
    <Sidebar />
    <div className="flex-1 flex flex-col overflow-hidden">
      <Navbar title={title} />
      <main className="flex-1 overflow-y-auto p-6">
        {children}
      </main>
    </div>
  </div>
);

export default PageLayout;
