import { AppProviders } from "./app/providers/AppProviders.tsx";
import { AppRouter } from "./app/router/index.tsx";
import { GlobalLoadingOverlay } from "./common/components/GlobalLoadingOverlay.tsx";

function App() {
  return (
    <AppProviders>
      <AppRouter />
      <GlobalLoadingOverlay />
    </AppProviders>
  );
}

export default App;
