import { request, resolveMediaUrl } from './apiClient';
import { VerificationReport } from '../types';

export const reportApi = {
  getReport: (reportId: string) =>
    request<VerificationReport>(`/reports/${reportId}`),

  deleteReport: (reportId: string) =>
    request<{ message: string; report_id: string }>(`/reports/${reportId}`, {
      method: 'DELETE',
    }),

  getPdfDownloadUrl: (reportId: string) =>
    resolveMediaUrl(`/api/v1/reports/${reportId}/pdf`),

  getHistory: (limit = 25, offset = 0) =>
    request<VerificationReport[]>(`/history?limit=${limit}&offset=${offset}`),
};
