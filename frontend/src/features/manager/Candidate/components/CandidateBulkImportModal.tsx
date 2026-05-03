import type { CandidateSampleFolder } from "../types";

interface CandidateBulkImportModalProps {
  open: boolean;
  folders: CandidateSampleFolder[];
  selectedFolderName: string;
  isLoadingFolders: boolean;
  isSubmitting: boolean;
  onClose: () => void;
  onFolderChange: (value: string) => void;
  onRefresh: () => void;
  onSubmit: () => void;
}

const panelClassName =
  "w-full max-w-xl rounded-[28px] border border-white/70 bg-white p-6 shadow-2xl";

const selectClassName =
  "mt-2 h-12 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)] disabled:cursor-not-allowed disabled:opacity-60";

export function CandidateBulkImportModal({
  open,
  folders,
  selectedFolderName,
  isLoadingFolders,
  isSubmitting,
  onClose,
  onFolderChange,
  onRefresh,
  onSubmit,
}: CandidateBulkImportModalProps) {
  if (!open) {
    return null;
  }

  const hasFolders = folders.length > 0;
  const placeholderLabel = isLoadingFolders
    ? "Loading folders..."
    : hasFolders
      ? "Select a folder"
      : "No folders available";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
      <div className={panelClassName}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-[var(--text)]">
              Bulk Candidate Import
            </h3>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Select one sample-data folder and register every candidate inside it at
              once.
            </p>
          </div>
          <button
            type="button"
            className="rounded-xl border border-[var(--line)] px-3 py-2 text-sm font-semibold text-[var(--muted)] transition hover:bg-slate-50"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Close
          </button>
        </div>

        <div className="mt-5 rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm font-semibold text-[var(--text)]">
              Sample folder
            </span>
            <button
              type="button"
              className="rounded-xl border border-[var(--line)] px-3 py-2 text-sm font-semibold text-[var(--text)] transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
              onClick={onRefresh}
              disabled={isLoadingFolders || isSubmitting}
            >
              Refresh
            </button>
          </div>

          <label className="mt-3 block text-sm font-medium text-[var(--text)]">
            Folder to import
            <select
              className={selectClassName}
              value={selectedFolderName}
              onChange={(event) => onFolderChange(event.target.value)}
              disabled={isLoadingFolders || isSubmitting || !hasFolders}
            >
              <option value="">{placeholderLabel}</option>
              {folders.map((folder) => (
                <option key={folder.folderName} value={folder.folderName}>
                  {folder.folderName} ({folder.candidateCount})
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            className="inline-flex h-11 items-center justify-center rounded-xl border border-[var(--line)] px-4 text-sm font-semibold text-[var(--text)] transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="button"
            className="inline-flex h-11 items-center justify-center rounded-xl border border-transparent bg-[var(--primary)] px-4 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            onClick={onSubmit}
            disabled={isSubmitting || isLoadingFolders || !selectedFolderName}
          >
            {isSubmitting ? "Importing..." : "Run import"}
          </button>
        </div>
      </div>
    </div>
  );
}
