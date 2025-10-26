// Main App component - React Router setup and tab routing
// This is the entry point for our harmonic analysis frontend

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import TabNavigation from './components/TabNavigation';
import Tab1 from './tabs/Tab1';
import Tab2 from './tabs/Tab2';

function App() {
  return (
    <Router>
      <Layout>
        <TabNavigation />
        <Routes>
          <Route path="/" element={<Tab1 />} />
          <Route path="/upload" element={<Tab2 />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
