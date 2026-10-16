import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Search, Globe, Image as ImageIcon, Film, Volume2, Shield } from 'lucide-react';
import { ClaimInput } from '../../components/ClaimInput';
import { NewsUrlInput } from '../../components/NewsUrlInput';
import { ImageUploader } from '../../components/ImageUploader';
import { VideoUploader } from '../../components/VideoUploader';
import { AudioUploader } from '../../components/AudioUploader';
import { ProcessingProgress } from '../../components/ProcessingProgress';
import { verificationApi } from '../../services/verificationApi';
import { InputType } from '../../types';

export const VerifyPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const queryJobId = searchParams.get('jobId');
  const queryTab = searchParams.get('tab') as InputType | null;

  const [activeTab, setActiveTab] = useState<InputType>(
    queryTab && ['claim', 'url', 'image', 'video', 'audio'].includes(queryTab) ? queryTab : 'claim'
  );
  const [activeJobId, setActiveJobId] = useState<string | null>(queryJobId);
  const [isLoading, setIsLoading] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  useEffect(() => {
    if (queryJobId) {
      setActiveJobId(queryJobId);
    }
  }, [queryJobId]);

  useEffect(() => {
    if (queryTab && ['claim', 'url', 'image', 'video', 'audio'].includes(queryTab)) {
      setActiveTab(queryTab);
    }
  }, [queryTab]);

  const handleClaimSubmit = async (claimText: string, context?: string) => {
    setIsLoading(true);
    setSubmissionError(null);
    try {
      const job = await verificationApi.verifyClaim(claimText, context);
      setActiveJobId(job.id);
      setSearchParams({ jobId: job.id });
    } catch (err: any) {
      setSubmissionError(err.message || 'Failed to submit claim.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUrlSubmit = async (url: string) => {
    setIsLoading(true);
    setSubmissionError(null);
    try {
      const job = await verificationApi.verifyUrl(url);
      setActiveJobId(job.id);
      setSearchParams({ jobId: job.id });
    } catch (err: any) {
      setSubmissionError(err.message || 'Failed to submit article URL.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageSubmit = async (file: File, context?: string) => {
    setIsLoading(true);
    setSubmissionError(null);
    try {
      const job = await verificationApi.verifyImage(file, context);
      setActiveJobId(job.id);
      setSearchParams({ jobId: job.id });
    } catch (err: any) {
      setSubmissionError(err.message || 'Failed to upload image.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVideoSubmit = async (file: File) => {
    setIsLoading(true);
    setSubmissionError(null);
    try {
      const job = await verificationApi.verifyVideo(file);
      setActiveJobId(job.id);
      setSearchParams({ jobId: job.id });
    } catch (err: any) {
      setSubmissionError(err.message || 'Failed to upload video.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAudioSubmit = async (file: File) => {
    setIsLoading(true);
    setSubmissionError(null);
    try {
      const job = await verificationApi.verifyAudio(file);
      setActiveJobId(job.id);
      setSearchParams({ jobId: job.id });
    } catch (err: any) {
      setSubmissionError(err.message || 'Failed to upload audio.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleJobComplete = (reportId: string) => {
    navigate(`/results/${reportId}`);
  };

  const tabs = [
    {
      id: 'claim' as InputType,
      label: 'Text Claim',
      icon: Search,
      desc: 'Verify if an assertion, rumor, or quote is factually true or false'
    },
    {
      id: 'url' as InputType,
      label: 'News URL',
      icon: Globe,
      desc: 'Scrape and verify claims and publisher credibility for web articles'
    },
    {
      id: 'image' as InputType,
      label: 'Image Forensics',
      icon: ImageIcon,
      desc: 'Detect generative AI synthesis, Photoshop splicing, and metadata anomalies'
    },
    {
      id: 'video' as InputType,
      label: 'Video Scan',
      icon: Film,
      desc: 'Examine videos for deepfake face swaps and frame-to-frame inconsistencies'
    },
    {
      id: 'audio' as InputType,
      label: 'Audio Forensics',
      icon: Volume2,
      desc: 'Detect synthetic voice clones, speech frequency anomalies, and transcripts'
    },
  ];

  const currentTabInfo = tabs.find(t => t.id === activeTab) || tabs[0];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
          Verify Media & Claims
        </h1>
        <p className="text-sm text-slate-600 max-w-lg mx-auto">
          Select an inspection category below to run automated cross-referencing and forensic checks.
        </p>
      </div>

      {/* If a job is currently executing, display live progress */}
      {activeJobId ? (
        <div className="space-y-4">
          <ProcessingProgress
            jobId={activeJobId}
            onComplete={handleJobComplete}
            onError={(err) => setSubmissionError(err)}
            onReset={() => {
              setActiveJobId(null);
              setSearchParams({});
              setSubmissionError(null);
            }}
          />
          <div className="text-center">
            <button
              onClick={() => {
                setActiveJobId(null);
                setSearchParams({});
              }}
              className="text-xs font-medium text-slate-500 hover:text-slate-800 underline transition-colors cursor-pointer"
            >
              Cancel and check something else
            </button>
          </div>
        </div>
      ) : (
        /* Input Workbench with Clean Tabs */
        <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          {/* Tabs */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5 p-1 bg-slate-100 rounded-lg border border-slate-200">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setSearchParams({ tab: tab.id });
                    setSubmissionError(null);
                  }}
                  className={`py-2 px-3 rounded-md text-xs font-medium flex items-center justify-center space-x-1.5 transition-colors cursor-pointer ${
                    isActive
                      ? 'bg-white text-blue-600 shadow-xs font-semibold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Current Tab Info */}
          <div className="p-3 rounded-md bg-slate-50 border border-slate-200 text-xs text-slate-600">
            <span className="font-semibold text-slate-800">{currentTabInfo.label}:</span> {currentTabInfo.desc}
          </div>

          {/* Submission Error Banner */}
          {submissionError && (
            <div className="p-3.5 rounded-md bg-red-50 border border-red-200 text-red-700 text-xs">
              {submissionError}
            </div>
          )}

          {/* Tab Content Panels */}
          <div className="pt-2">
            {activeTab === 'claim' && (
              <ClaimInput onSubmit={handleClaimSubmit} isLoading={isLoading} />
            )}
            {activeTab === 'url' && (
              <NewsUrlInput onSubmit={handleUrlSubmit} isLoading={isLoading} />
            )}
            {activeTab === 'image' && (
              <ImageUploader onSubmit={handleImageSubmit} isLoading={isLoading} />
            )}
            {activeTab === 'video' && (
              <VideoUploader onSubmit={handleVideoSubmit} isLoading={isLoading} />
            )}
            {activeTab === 'audio' && (
              <AudioUploader onSubmit={handleAudioSubmit} isLoading={isLoading} />
            )}
          </div>
        </div>
      )}
    </div>
  );
};
