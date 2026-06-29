import { BrowserRouter, Route, Routes } from "react-router-dom";
import HomePage from "./Home";
import JournalPage from "./Journal";

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/journals/:slug" element={<JournalPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
