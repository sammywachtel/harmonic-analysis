// App entry — three tabs sit under one Layout: Manual entry, Notation upload,
// Audio analysis. Routing is plain React Router; per-tab state stays local.

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import TabNavigation from './components/TabNavigation';
import Tab1 from './tabs/Tab1';
import Tab2 from './tabs/Tab2';
import Tab3 from './tabs/Tab3';

function App() {
  return (
    <Router>
      <Layout>
        <TabNavigation />
        <Routes>
          <Route path="/" element={<Tab1 />} />
          <Route path="/upload" element={<Tab2 />} />
          <Route path="/audio" element={<Tab3 />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
