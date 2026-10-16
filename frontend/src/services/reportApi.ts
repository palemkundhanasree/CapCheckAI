import { request, requestBlob } from './apiClient';
import { VerificationReport } from '../types';

export const reportApi = {
  getReport: (reportId: string) =>
    request<VerificationReport>(`/reports/${reportId}`),

  deleteReport: (reportId: string) =>
    request<{ message: string; report_id: string }>(`/reports/${reportId}`, {
      method: 'DELETE',
    }),

  getPdfBlob: (reportId: string) => requestBlob(`/reports/${reportId}/pdf`),

  getMediaBlob: (reportId: string) => requestBlob(`/reports/${reportId}/media`),

  getHistory: (limit = 25, offset = 0) =>
    request<VerificationReport[]>(`/history?limit=${limit}&offset=${offset}`),
};
