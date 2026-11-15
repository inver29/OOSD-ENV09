import { useSearchParams } from "react-router-dom";
import Loans from "./Loans";
import Needs from "./Needs";
import Indicator from "./Indicator";

export function Borrowing() {
  const [params, setParams] = useSearchParams();
  const needs = params.get("tab") === "needs";
  return (
    <>
      <div className="workspace-tabs" aria-label="Mượn và nhu cầu">
        <button
          className={!needs ? "active" : ""}
          onClick={() => setParams({})}
        >
          Phiếu mượn
        </button>
        <button
          className={needs ? "active" : ""}
          onClick={() => setParams({ tab: "needs" })}
        >
          Nhu cầu sử dụng
        </button>
      </div>
      {needs ? <Needs /> : <Loans />}
    </>
  );
}

export function Effectiveness() {
  const [params, setParams] = useSearchParams();
  const indicator = params.get("tab") === "indicator";
  return (
    <>
      <div className="workspace-tabs" aria-label="Hiệu quả sử dụng">
        <button
          className={!indicator ? "active" : ""}
          onClick={() => setParams({})}
        >
          Xác minh nhu cầu
        </button>
        <button
          className={indicator ? "active" : ""}
          onClick={() => setParams({ tab: "indicator" })}
        >
          Chỉ số tránh mua mới
        </button>
      </div>
      {indicator ? <Indicator /> : <Needs manage />}
    </>
  );
}
