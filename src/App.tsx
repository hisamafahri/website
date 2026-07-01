import { BrowserRouter, Route, Routes } from "react-router-dom";
import HomePage from "./Home";
import JournalPage from "./Journal";
import NotFoundPage from "./NotFound";

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/journals/:slug" element={<JournalPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
