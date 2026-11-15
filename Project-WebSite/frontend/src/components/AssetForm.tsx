import { useState } from "react";
import { send } from "../api";
import { useAuth, useToast } from "../context";
import type { Asset } from "../types";
import { ActionForm, Attachment, Field, Modal } from "./ui";
export default function AssetForm({
  asset,
  onClose,
  onSaved,
}: {
  asset?: Asset;
  onClose: () => void;
  onSaved: (a: Asset) => void;
}) {
  const { lookups, user } = useAuth();
  const toast = useToast();
  const [name, setName] = useState(asset?.name || ""),
    [category, setCategory] = useState(asset?.category_id || 0),
    [location, setLocation] = useState(asset?.location_id || 0),
    [description, setDescription] = useState(asset?.description || ""),
    [condition, setCondition] = useState(asset?.condition || ""),
    [image, setImage] = useState(asset?.image_path || null),
    [uploading, setUploading] = useState(false);
  return (
    <Modal
      title={asset ? "Chỉnh sửa tài sản" : "Đăng ký tài sản"}
      onClose={onClose}
    >
      <ActionForm
        disabled={uploading}
        onCancel={onClose}
        submitLabel={
          asset
            ? asset.status === "TU_CHOI"
              ? "Gửi lại duyệt"
              : "Lưu hồ sơ"
            : "Thêm"
        }
        onSubmit={async () => {
          const saved = await send<Asset>(
            asset ? `/assets/${asset.id}` : "/assets",
            {
              name,
              category_id: category,
              location_id: location,
              description,
              condition,
              image_path: image,
              version: asset?.version || null,
            },
            asset ? "PUT" : "POST",
          );
          toast(
            !asset && saved.status === "CHO_CHIA_SE"
              ? "Đã thêm tài sản và tự động duyệt chia sẻ."
              : !asset || asset.status === "TU_CHOI"
                ? "Đã gửi tài sản, chờ quản lý chi nhánh duyệt."
                : "Đã lưu hồ sơ tài sản.",
          );
          onSaved(saved);
        }}
      >
        <div className="form-grid">
          <Field label="Tên tài sản *" wide>
            <input
              required
              maxLength={200}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </Field>
          <Field label="Loại tài sản *">
            <select
              required
              value={category}
              onChange={(e) => setCategory(+e.target.value)}
            >
              <option value={0} disabled>
                Chọn loại
              </option>
              {lookups?.categories
                .filter((x) => x.active)
                .map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.name}
                  </option>
                ))}
            </select>
          </Field>
          <Field label="Địa điểm *">
            <select
              required
              value={location}
              onChange={(e) => setLocation(+e.target.value)}
            >
              <option value={0} disabled>
                Chọn địa điểm
              </option>
              {lookups?.locations
                .filter((x) => x.active && x.unit_id === user?.unit_id)
                .map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.name}
                  </option>
                ))}
            </select>
          </Field>
          <Field label="Người phụ trách" wide>
            <input readOnly value={asset?.custodian_name || user?.name || ""} />
          </Field>
          <Field label="Đặc tính / Phụ kiện" wide>
            <textarea
              maxLength={1000}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </Field>
          <Field label="Tình trạng hiện tại *" wide>
            <textarea
              required
              minLength={2}
              maxLength={500}
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
              rows={2}
            />
          </Field>
          <Field label="Ảnh tài sản" wide>
            <Attachment
              imageOnly
              value={image}
              onChange={setImage}
              onBusyChange={setUploading}
            />
          </Field>
        </div>
      </ActionForm>
    </Modal>
  );
}
