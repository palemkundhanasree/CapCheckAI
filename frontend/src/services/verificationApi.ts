import { request } from './apiClient';
import { JobStatus, JobListResponse, HealthStatus } from '../types';

export const verificationApi = {
  getHealth: () => request<HealthStatus>('/health'),

  verifyClaim: (claim_text: string, context?: string) =>
    request<JobStatus>('/verify/claim', {
      method: 'POST',
      body: JSON.stringify({ claim_text, context }),
    }),

  verifyUrl: (url: string) =>
    request<JobStatus>('/verify/url', {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),

  verifyImage: (file: File, context?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (context) formData.append('context', context);
    return request<JobStatus>('/verify/image', {
      method: 'POST',
      body: formData,
    });
  },

  verifyVideo: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<JobStatus>('/verify/video', {
      method: 'POST',
      body: formData,
    });
  },

  verifyAudio: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<JobStatus>('/verify/audio', {
      method: 'POST',
      body: formData,
    });
  },

  getJobStatus: (jobId: string) =>
    request<JobStatus>(`/jobs/${jobId}`),

  getRecentJobs: (limit = 20) =>
    request<JobListResponse>(`/jobs?limit=${limit}`),
};
