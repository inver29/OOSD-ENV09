import {
  useEffect,
  isValidElement,
  useRef,
  useState,
  type ReactNode,
  type FormEvent,
} from "react";
import { createPortal } from "react-dom";
import {
  Camera,
  Monitor,
  Printer,
  Projector,
  LoaderCircle,
  PackageOpen,
  Upload,
  X,
  Check,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { errorText, label, handoverLabels } from "../utils";
import { upload } from "../api";

let modalCount = 0;
let bodyOverflow = "";

export function Badge({
  status,
  overdue = false,
  entity,
}: {
  status: string;
  overdue?: boolean;
  entity?: "handover";
}) {
  const color = ["TU_CHOI", "DA_THU_HOI", "HET_HAN_NHAN"].includes(status)
    ? "red"
    : [
          "CHO_DUYET",
          "CHO_XAC_NHAN_TRA",
          "CHO_XAC_MINH",
          "BAO_TRI",
          "CHO_THU_HOI",
          "CHO_XAC_NHAN",
          "CHO_BAN_GIAO",
        ].includes(status)
      ? "amber"
      : ["CHO_CHIA_SE", "DA_HOAN_TRA", "HOAN_TAT", "DA_XAC_MINH"].includes(status)
        ? "green"
        : ["DANG_MUON", "DA_DUOC_MUON"].includes(status)
          ? "blue"
          : "gray";
  const badge = (
    <span className={`badge ${color}`}>
      <span />
      {entity === "handover"
        ? handoverLabels[status] || label(status)
        : label(status)}
    </span>
  );
  return overdue ? (
    <span className="status-badges">
      {badge}
      <span className="badge red">
        <span />
        Quá hạn trả
      </span>
    </span>
  ) : (
    badge
  );
}
export function Loading() {
  return (
    <div className="state">
      <LoaderCircle className="spin" />
      <span>Đang tải dữ liệu…</span>
    </div>
  );
}
export function Empty({
  text = "Chưa có dữ liệu.",
  action,
}: {
  text?: string;
  action?: ReactNode;
}) {
  return (
    <div className="state empty">
      <PackageOpen size={36} />
      <p>{text}</p>
      {action}
    </div>
  );
}
export function ErrorBox({ message }: { message: string }) {
  return message ? (
    <div role="alert" className="error-box">
      {message}
    </div>
  ) : null;
}
export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action && <div className="heading-action">{action}</div>}
    </div>
  );
}
export function Field({
  label: caption,
  children,
  wide = false,
  hint,
}: {
  label: string;
  children: ReactNode;
  wide?: boolean;
  hint?: string;
}) {
  const nativeControl =
    isValidElement(children) &&
    typeof children.type === "string" &&
    ["input", "select", "textarea"].includes(children.type);
  const Wrapper = nativeControl ? "label" : "div";
  return (
    <Wrapper
      className={`field ${wide ? "wide" : ""}`}
      role={nativeControl ? undefined : "group"}
      aria-label={nativeControl ? undefined : caption}
    >
      <span>{caption}</span>
      {children}
      {hint && <small>{hint}</small>}
    </Wrapper>
  );
}
export function Modal({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    if (modalCount === 0) bodyOverflow = document.body.style.overflow;
    modalCount += 1;
    document.body.style.overflow = "hidden";
    ref.current?.focus();
    const key = (e: KeyboardEvent) => {
      const dialogs = document.querySelectorAll('[role="dialog"]');
      if (dialogs[dialogs.length - 1] !== ref.current) return;
      if (e.key === "Escape") closeRef.current();
      if (e.key === "Tab" && ref.current) {
        const nodes = Array.from(
          ref.current.querySelectorAll<HTMLElement>(
            "button,input,select,textarea,a[href],iframe,[tabindex]",
          ),
        ).filter(
          (node) =>
            node.tabIndex >= 0 &&
            !node.matches(":disabled") &&
            node.getClientRects().length > 0,
        );
        const first = nodes[0],
          last = nodes[nodes.length - 1];
        if (!first || (e.shiftKey && document.activeElement === ref.current)) {
          e.preventDefault();
          last?.focus();
        } else if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", key);
    return () => {
      modalCount -= 1;
      if (modalCount === 0) document.body.style.overflow = bodyOverflow;
      document.removeEventListener("keydown", key);
      if (previous?.isConnected) previous.focus();
    };
  }, []);
  return createPortal(
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className={`modal ${wide ? "modal-wide" : ""}`}
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
      >
        <div className="modal-header">
          <h2>{title}</h2>
          <button
            type="button"
            className="icon-button"
            onClick={onClose}
            aria-label="Đóng hộp thoại"
          >
            <X />
          </button>
        </div>
        {children}
      </div>
    </div>,
    document.body,
  );
}
export function ActionForm({
  children,
  onSubmit,
  submitLabel = "Lưu thay đổi",
  onCancel,
  disabled = false,
}: {
  children: ReactNode;
  onSubmit: () => Promise<void>;
  submitLabel?: string;
  onCancel?: () => void;
  disabled?: boolean;
}) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy || disabled) return;
    setBusy(true);
    setError("");
    try {
      await onSubmit();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  };
  return (
    <form onSubmit={submit}>
      <fieldset disabled={busy || disabled} className="form-fields">
        {children}
        <ErrorBox message={error} />
        <div className="form-actions">
          {onCancel && (
            <button type="button" className="btn secondary" onClick={onCancel}>
              Đóng
            </button>
          )}
          <button className="btn primary" type="submit">
            {busy ? (
              <LoaderCircle size={17} className="spin" />
            ) : (
              <Check size={17} />
            )}{" "}
            {busy ? "Đang lưu…" : submitLabel}
          </button>
        </div>
      </fieldset>
    </form>
  );
}
export function Attachment({
  value,
  onChange,
  imageOnly = false,
  onBusyChange,
}: {
  value: string | null;
  onChange: (s: string | null) => void;
  imageOnly?: boolean;
  onBusyChange?: (busy: boolean) => void;
}) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [preview, setPreview] = useState<string | null>(null);
  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview);
    },
    [preview],
  );
  const image =
    preview ||
    (value && /\.(png|jpg|jpeg|webp)$/i.test(value)
      ? `/api/files/${value}`
      : null);
  return (
    <div className="upload-field">
      <div className="inline-actions">
        {value && (
          <>
            <FileLink file={value}>Xem tệp đã đính kèm</FileLink>
            <button
              type="button"
              className="icon-button"
              aria-label="Bỏ tệp"
              onClick={() => {
                setPreview(null);
                onChange(null);
              }}
            >
              <X size={16} />
            </button>
          </>
        )}
        <label className="btn secondary small">
          <Upload size={16} />
          {busy ? "Đang tải…" : value ? "Thay tệp" : "Đính kèm tệp"}
          <input
            type="file"
            hidden
            disabled={busy}
            accept={
              imageOnly
                ? "image/png,image/jpeg,image/webp"
                : "image/png,image/jpeg,image/webp,application/pdf"
            }
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              setBusy(true);
              onBusyChange?.(true);
              setError("");
              try {
                if (file.size > 8 * 1024 * 1024)
                  throw new Error("Tệp tối đa 8 MB.");
                if (imageOnly && !file.type.startsWith("image/"))
                  throw new Error("Ảnh tài sản cần là PNG, JPG hoặc WEBP.");
                if (file.type.startsWith("image/"))
                  setPreview(URL.createObjectURL(file));
                onChange((await upload(file)).filename);
              } catch (err) {
                setPreview(null);
                setError(errorText(err));
              } finally {
                setBusy(false);
                onBusyChange?.(false);
                e.target.value = "";
              }
            }}
          />
        </label>
      </div>
      {image && (
        <div className="attachment-preview">
          <img src={image} alt="Ảnh đã chọn" />
        </div>
      )}
      {error && <small className="error-text">{error}</small>}
    </div>
  );
}

export function FileLink({
  file,
  children,
}: {
  file: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  const pdf = file.toLowerCase().endsWith(".pdf");
  return (
    <>
      <button
        type="button"
        className="text-link file-link"
        onClick={() => {
          setFailed(false);
          setOpen(true);
        }}
      >
        {children}
      </button>
      {open && (
        <Modal
          title={pdf ? "Xem chứng từ" : "Xem ảnh"}
          wide
          onClose={() => setOpen(false)}
        >
          <div className="file-preview">
            {pdf ? (
              <iframe title="Chứng từ PDF" src={`/api/files/${file}`} />
            ) : failed ? (
              <ErrorBox message="Không tải được ảnh. Vui lòng thử lại." />
            ) : (
              <img
                src={`/api/files/${file}`}
                alt="Ảnh / Chứng từ"
                onError={() => setFailed(true)}
              />
            )}
          </div>
          <div className="form-actions">
            <button
              type="button"
              className="btn secondary"
              onClick={() => setOpen(false)}
            >
              Đóng
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
export function DeviceArt({
  category,
  name = "",
  image,
  large = false,
}: {
  category: string;
  name?: string;
  image?: string | null;
  large?: boolean;
}) {
  const Icon = category.includes("trình")
    ? Projector
    : category.includes("ảnh")
      ? Camera
      : category.includes("văn")
        ? Printer
        : Monitor;
  return (
    <div
      className={`device-art ${large ? "large" : ""} device-${Icon === Camera ? "camera" : Icon === Projector ? "projector" : Icon === Printer ? "printer" : "monitor"}`}
    >
      {image ? (
        <img src={`/api/files/${image}`} alt={name} />
      ) : (
        <>
          <div className="art-orbit" />
          <Icon size={large ? 100 : 70} strokeWidth={1.1} />
          <span className="art-shadow" />
        </>
      )}
    </div>
  );
}
export function Pagination({
  page,
  total,
  size = 12,
  onChange,
}: {
  page: number;
  total: number;
  size?: number;
  onChange: (n: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / size));
  return (
    <div className="pagination">
      <span>{total} kết quả</span>
      <div>
        <button
          className="icon-button"
          disabled={page === 1}
          aria-label="Trang trước"
          onClick={() => onChange(page - 1)}
        >
          <ChevronLeft size={18} />
        </button>
        <span>
          {page} / {pages}
        </span>
        <button
          className="icon-button"
          disabled={page >= pages}
          aria-label="Trang sau"
          onClick={() => onChange(page + 1)}
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  );
}
export function DataItem({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="data-item">
      <span>{title}</span>
      <div>{children || "—"}</div>
    </div>
  );
}
