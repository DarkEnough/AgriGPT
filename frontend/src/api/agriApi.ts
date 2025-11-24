import { apiClient } from "./client";

export interface ApiResponse {
  analysis: string;
  request_id?: string;
  status?: string;
  input?: any;
}

interface FormDataPayload {
  [key: string]: string | Blob | undefined;
}

/**
 * Utility: Build FormData safely
 */
function buildFormData(payload: FormDataPayload): FormData {
  const fd = new FormData();
  Object.entries(payload).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      fd.append(key, value);
    }
  });
  return fd;
}

/**
 * Utility: Handle API POST request
 */
async function postFormData(
  url: string,
  formData: FormData
): Promise<ApiResponse> {
  const res = await apiClient.post<ApiResponse>(url, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

/**
 * Utility: Handle JSON POST request
 */
async function postJson<TBody extends object>(
  url: string,
  body: TBody
): Promise<ApiResponse> {
  // The backend /ask/text endpoint expects FORM DATA for the 'query' field,
  // NOT JSON body.
  // But wait, looking at the backend code:
  // async def ask_text(query: str = Form(...))
  // So we must use FormData or x-www-form-urlencoded, NOT application/json.
  
  const fd = new FormData();
  // @ts-ignore
  if (body.query) fd.append("query", body.query);

  const res = await apiClient.post<ApiResponse>(url, fd);
  return res.data;
}

/** Text-only request */
export const askText = (query: string): Promise<ApiResponse> =>
  postJson("/ask/text", { query: query.trim() });

/**  Image-only diagnosis */
export const askImage = (image: File): Promise<ApiResponse> =>
  postFormData("/ask/image", buildFormData({ image }));

/**  Multimodal: text + image */
export const askChat = (
  query: string,
  image?: File
): Promise<ApiResponse> => {
  const payload = buildFormData({
    query: query.trim(),
    image,
  });

  return postFormData("/ask/chat", payload);
};
