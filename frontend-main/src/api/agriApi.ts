import { apiClient } from "./client";
import { v4 as uuidv4 } from 'uuid'; // Note: You might need to install uuid or use a simple generator

export interface ApiResponse {
  analysis: string;
  request_id?: string;
  status?: string;
  input?: any;
}

interface FormDataPayload {
  [key: string]: string | Blob | undefined;
}

// --- Session Management ---
const SESSION_KEY = 'agrigpt_session_id';

function getSessionId(): string {
  let sid = localStorage.getItem(SESSION_KEY);
  if (!sid) {
    // Simple UUID generator if uuid package isn't available
    sid = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).substr(2);
    localStorage.setItem(SESSION_KEY, sid);
  }
  return sid;
}
// --------------------------

/**
 * Utility: Build FormData safely
 */
function buildFormData(payload: FormDataPayload): FormData {
  const fd = new FormData();
  
  // Auto-inject session_id
  fd.append("session_id", getSessionId());

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

/** Text-only request */
export const askText = (query: string): Promise<ApiResponse> => {
  // We reuse buildFormData to ensure session_id is added
  const payload = buildFormData({ query: query.trim() });
  return postFormData("/ask/text", payload);
}

/**  Image-only diagnosis */
export const askImage = (image: File): Promise<ApiResponse> =>
  postFormData("/ask/image", buildFormData({ file: image }));

/**  Multimodal: text + image */
export const askChat = (
  query: string,
  image?: File
): Promise<ApiResponse> => {
  const payloadObj: FormDataPayload = {
    query: query.trim(),
  };

  if (image) {
    payloadObj.file = image;
  }

  const payload = buildFormData(payloadObj);
  return postFormData("/ask/chat", payload);
};
