import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Clock,
  Send,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  RotateCcw
} from 'lucide-react';
import { api } from '../services/api';
import {
  QuestionPublicResponse,
  AnswerEvaluationResponse,
  InterviewSessionResponse,
  InterviewProgressResponse
} from '../types';

export const InterviewDashboardPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<InterviewSessionResponse | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<QuestionPublicResponse | null>(null);
  const [progress, setProgress] = useState<InterviewProgressResponse | null>(null);
  const [answerText, setAnswerText] = useState<string>('');

  const [evaluation, setEvaluation] = useState<AnswerEvaluationResponse | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [advancing, setAdvancing] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const timerRef = useRef<any>(null);

  // --- VOICE FEATURES: TTS (Text-to-Speech) & STT (Speech-to-Text) ---
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [autoSpeak, setAutoSpeak] = useState<boolean>(false);
  const ttsSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;

  const [isListening, setIsListening] = useState<boolean>(false);
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [speechError, setSpeechError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  const sttSupported =
    typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  const speakText = (text: string) => {
    if (!ttsSupported) return;

    window.speechSynthesis.cancel();

    if (isSpeaking) {
      setIsSpeaking(false);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.lang = 'en-US';

    const voices = window.speechSynthesis.getVoices();
    const naturalVoice = voices.find(
      (v) =>
        v.lang.startsWith('en') &&
        (v.name.includes('Natural') ||
          v.name.includes('Google') ||
          v.name.includes('Neural') ||
          v.name.includes('Samantha') ||
          v.name.includes('David') ||
          v.name.includes('English'))
    );
    if (naturalVoice) utterance.voice = naturalVoice;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if (!ttsSupported) return;
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  };

  const startListening = () => {
    if (!sttSupported) {
      setSpeechError('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    stopSpeaking();
    setSpeechError(null);

    try {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;

      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
        setSpeechError(null);
      };

      recognition.onresult = (event: any) => {
        let finalStr = '';
        let interimStr = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcript = event.results[i][0]?.transcript || '';
          if (event.results[i].isFinal) {
            finalStr += transcript;
          } else {
            interimStr += transcript;
          }
        }

        setInterimTranscript(interimStr);

        if (finalStr.trim()) {
          setAnswerText((prev) => {
            const trimmedPrev = prev.trim();
            const spacer = trimmedPrev.length > 0 ? ' ' : '';
            return trimmedPrev + spacer + finalStr.trim();
          });
        }
      };

      recognition.onerror = (event: any) => {
        if (event.error === 'not-allowed') {
          setSpeechError('Microphone permission was denied. Please allow microphone access in your browser bar.');
        } else if (event.error !== 'no-speech') {
          setSpeechError(`Voice input notice: ${event.error}`);
        }
        setIsListening(false);
        setInterimTranscript('');
      };

      recognition.onend = () => {
        setIsListening(false);
        setInterimTranscript('');
      };

      recognition.start();
    } catch (err: any) {
      setSpeechError(err.message || 'Could not access microphone.');
      setIsListening(false);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        // ignore
      }
    }
    setIsListening(false);
    setInterimTranscript('');
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // Cleanup audio & speech recognition on unmount
  useEffect(() => {
    return () => {
      if (ttsSupported) window.speechSynthesis.cancel();
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // ignore
        }
      }
    };
  }, [ttsSupported]);

  // Auto-speak question if enabled
  useEffect(() => {
    if (autoSpeak && currentQuestion?.question_text && !evaluation) {
      const timer = setTimeout(() => {
        speakText(currentQuestion.question_text);
      }, 350);
      return () => clearTimeout(timer);
    }
  }, [currentQuestion?.id, autoSpeak, evaluation]);

  useEffect(() => {
    if (!sessionId) return;

    const loadSessionAndQuestion = async () => {
      setLoading(true);
      setError(null);
      try {
        const [sessionData, questionData, progressData] = await Promise.all([
          api.getInterview(sessionId),
          api.getCurrentQuestion(sessionId),
          api.getInterviewProgress(sessionId),
        ]);

        setSession(sessionData);
        setCurrentQuestion(questionData);
        setProgress(progressData);
      } catch (err: any) {
        setError(err.message || 'Failed to load interview session.');
      } finally {
        setLoading(false);
      }
    };

    loadSessionAndQuestion();

    timerRef.current = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [sessionId]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSubmitAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sessionId || !currentQuestion || !answerText.trim()) return;

    stopSpeaking();
    stopListening();

    if (answerText.trim().split(/\s+/).length < 5) {
      setError('Please provide a substantive answer (at least 5 words).');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const evalRes = await api.submitAnswer(sessionId, currentQuestion.id, answerText);
      setEvaluation(evalRes);

      const progressRes = await api.getInterviewProgress(sessionId);
      setProgress(progressRes);
    } catch (err: any) {
      setError(err.message || 'Failed to evaluate answer. Your response was preserved.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNextQuestion = async () => {
    if (!sessionId) return;

    stopSpeaking();
    stopListening();

    setAdvancing(true);
    setError(null);
    try {
      const nextRes = await api.advanceNextQuestion(sessionId);

      if (nextRes.is_finished || !nextRes.question) {
        await api.completeInterview(sessionId);
        navigate(`/interviews/${sessionId}/report`);
      } else {
        setCurrentQuestion(nextRes.question);
        setProgress(nextRes.progress);
        setEvaluation(null);
        setAnswerText('');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load next question.');
    } finally {
      setAdvancing(false);
    }
  };


  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-2" />
        <p className="text-slate-500 text-sm">Loading interview question...</p>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <p className="text-red-600">Question not available.</p>
      </div>
    );
  }

  const wordCount = answerText.trim() ? answerText.trim().split(/\s+/).length : 0;
  const targetCount = progress?.target_question_count || session?.target_question_count || 5;

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
      {/* HEADER BAR */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-sm text-slate-900">
            Question {currentQuestion.sequence_number} of {targetCount}
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">
            {session?.job_role}
          </span>
        </div>

        <div className="flex items-center space-x-1.5 text-xs text-slate-500">
          <Clock className="w-3.5 h-3.5" />
          <span className="font-mono">{formatTime(elapsedSeconds)}</span>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* QUESTION CARD */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2.5">
          <div className="flex items-center space-x-2 text-xs">
            <span className="font-semibold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-full">
              {currentQuestion.competency_name}
            </span>
            <span className="text-slate-500 capitalize px-2 py-0.5 bg-slate-100 rounded-md">
              {currentQuestion.difficulty} level
            </span>
          </div>

          {/* Voice Controls: Listen to Question */}
          {ttsSupported && (
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() =>
                  isSpeaking
                    ? stopSpeaking()
                    : speakText(currentQuestion.question_text)
                }
                className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all ${
                  isSpeaking
                    ? 'bg-amber-100 text-amber-900 border border-amber-300 ring-2 ring-amber-200'
                    : 'bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200'
                }`}
                title={isSpeaking ? 'Click to stop reading' : 'Listen to interviewer read this question aloud'}
              >
                {isSpeaking ? (
                  <>
                    <VolumeX className="w-3.5 h-3.5 text-amber-700 shrink-0" />
                    <span>Stop Reading</span>
                    <span className="flex items-center space-x-0.5 ml-1">
                      <span className="w-1 h-2 bg-amber-600 rounded-full animate-bounce [animation-delay:0ms]" />
                      <span className="w-1 h-3.5 bg-amber-600 rounded-full animate-bounce [animation-delay:150ms]" />
                      <span className="w-1 h-2 bg-amber-600 rounded-full animate-bounce [animation-delay:300ms]" />
                    </span>
                  </>
                ) : (
                  <>
                    <Volume2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span>Listen to Question</span>
                  </>
                )}
              </button>

              <label className="flex items-center space-x-1.5 text-[11px] text-slate-500 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={autoSpeak}
                  onChange={(e) => setAutoSpeak(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500 w-3 h-3"
                />
                <span className="hidden sm:inline">Auto-read questions</span>
              </label>
            </div>
          )}
        </div>

        <h2 className="text-lg sm:text-xl font-bold text-slate-900 leading-snug">
          {currentQuestion.question_text}
        </h2>
      </div>

      {/* ANSWER BOX OR EVALUATION */}
      {!evaluation ? (
        <form onSubmit={handleSubmitAnswer} className="space-y-3">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500">
            {/* Live Listening Banner */}
            {isListening && (
              <div className="px-4 py-2 bg-gradient-to-r from-red-50 to-amber-50 border-b border-red-100 flex items-center justify-between text-xs text-red-800">
                <div className="flex items-center space-x-2">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-600" />
                  </span>
                  <span className="font-semibold">Microphone active:</span>
                  <span className="italic truncate max-w-xs sm:max-w-md">
                    {interimTranscript ? `"${interimTranscript}"` : 'Listening... speak clearly into your mic'}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={stopListening}
                  className="px-2 py-0.5 rounded bg-red-100 hover:bg-red-200 text-red-900 font-medium text-[11px]"
                >
                  Done Speaking
                </button>
              </div>
            )}

            {speechError && (
              <div className="px-4 py-2 bg-amber-50 border-b border-amber-200 text-amber-800 text-xs flex items-center justify-between">
                <span>{speechError}</span>
                <button
                  type="button"
                  onClick={() => setSpeechError(null)}
                  className="text-amber-600 font-bold ml-2"
                >
                  ×
                </button>
              </div>
            )}

            <textarea
              rows={7}
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              placeholder="Type your response here or click 'Speak Answer' below to speak your response using speech recognition..."
              className="w-full p-4 bg-white text-slate-900 placeholder:text-slate-400 text-sm leading-relaxed focus:outline-none resize-y min-h-[160px]"
              autoFocus
            />

            <div className="px-4 py-2.5 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
              <div className="flex items-center space-x-3">
                {/* Speech Recognition Mic Button */}
                {sttSupported ? (
                  <button
                    type="button"
                    onClick={toggleListening}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium text-xs transition-all ${
                      isListening
                        ? 'bg-red-600 text-white shadow-md ring-2 ring-red-300 animate-pulse'
                        : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 hover:border-blue-400'
                    }`}
                    title={isListening ? 'Click to stop recording' : 'Dictate your answer using your microphone'}
                  >
                    {isListening ? (
                      <>
                        <MicOff className="w-3.5 h-3.5 text-white" />
                        <span>Stop Voice Input</span>
                      </>
                    ) : (
                      <>
                        <Mic className="w-3.5 h-3.5 text-blue-600" />
                        <span>Speak Answer</span>
                      </>
                    )}
                  </button>
                ) : (
                  <span className="text-slate-400 text-[11px] italic">Mic STT not supported in browser</span>
                )}

                {answerText && (
                  <button
                    type="button"
                    onClick={() => setAnswerText('')}
                    className="flex items-center space-x-1 text-slate-400 hover:text-slate-600 transition-colors text-[11px]"
                    title="Clear answer text"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>Clear</span>
                  </button>
                )}

                <span>{wordCount} words</span>
              </div>

              <button
                type="submit"
                disabled={submitting || wordCount < 5}
                className="flex items-center space-x-1.5 px-4 py-1.5 rounded-md font-medium text-xs text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {submitting ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Grading answer...</span>
                  </>
                ) : (
                  <>
                    <span>Submit Answer</span>
                    <Send className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      ) : (
        /* EVALUATION FEEDBACK */
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div>
              <span className="text-xs font-semibold uppercase text-green-700">Answer Evaluated</span>
              <div className="text-xl font-bold text-slate-900">
                Score: {evaluation.weighted_score.toFixed(0)} <span className="text-sm font-normal text-slate-500">/ 100</span>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {ttsSupported && (
                <button
                  type="button"
                  onClick={() =>
                    isSpeaking
                      ? stopSpeaking()
                      : speakText(
                          `Your score is ${evaluation.weighted_score.toFixed(0)} out of 100. ${
                            evaluation.correct_concepts.length > 0
                              ? `You covered: ${evaluation.correct_concepts.join('. ')}.`
                              : ''
                          } ${
                            evaluation.missing_concepts.length > 0
                              ? `To improve, you could mention: ${evaluation.missing_concepts.join('. ')}.`
                              : ''
                          }`
                        )
                  }
                  className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
                  title="Listen to feedback"
                >
                  {isSpeaking ? (
                    <>
                      <VolumeX className="w-3.5 h-3.5 text-amber-600" />
                      <span>Stop</span>
                    </>
                  ) : (
                    <>
                      <Volume2 className="w-3.5 h-3.5 text-blue-600" />
                      <span>Hear Feedback</span>
                    </>
                  )}
                </button>
              )}

              <button
                type="button"
                onClick={handleNextQuestion}
                disabled={advancing}
                className="flex items-center space-x-1.5 px-4 py-2 rounded-lg font-medium text-xs text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors"
              >
                {advancing ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Loading...</span>
                  </>
                ) : (
                  <>
                    <span>
                      {currentQuestion.sequence_number >= targetCount
                        ? 'Finish & View Report'
                        : 'Next Question'}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </div>


          {/* 4 RUBRIC SCORES */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[11px] text-slate-500 block">Technical (40%)</span>
              <span className="text-base font-bold text-blue-700">{evaluation.technical_score.toFixed(0)}%</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[11px] text-slate-500 block">Depth (25%)</span>
              <span className="text-base font-bold text-slate-800">{evaluation.completeness_score.toFixed(0)}%</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[11px] text-slate-500 block">Relevance (20%)</span>
              <span className="text-base font-bold text-slate-800">{evaluation.relevance_score.toFixed(0)}%</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[11px] text-slate-500 block">Clarity (15%)</span>
              <span className="text-base font-bold text-slate-800">{evaluation.communication_score.toFixed(0)}%</span>
            </div>
          </div>

          {/* KEY POINTS & OMISSIONS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-green-50 border border-green-200 space-y-1">
              <div className="font-semibold text-green-800 flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
                <span>What was covered well</span>
              </div>
              {evaluation.correct_concepts.length > 0 ? (
                <ul className="space-y-0.5 text-green-900 list-disc list-inside">
                  {evaluation.correct_concepts.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-500 italic">No specific key points matched.</p>
              )}
            </div>

            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 space-y-1">
              <div className="font-semibold text-amber-800 flex items-center space-x-1">
                <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
                <span>Points to improve</span>
              </div>
              {evaluation.missing_concepts.length > 0 ? (
                <ul className="space-y-0.5 text-amber-900 list-disc list-inside">
                  {evaluation.missing_concepts.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-500 italic">All key rubric points addressed.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
