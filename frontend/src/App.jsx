import { useCallback, useEffect, useState } from 'react';
import { BlockMath } from 'react-katex';
import api from './api';
import 'katex/dist/katex.min.css';

const DEFAULT_USERNAME = 'Player1';
const PREFERRED_MACRO = 'Ułamki Zwykłe';

function App() {
  const [gameState, setGameState] = useState(null);
  const [problem, setProblem] = useState(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState(null);
  const [curriculum, setCurriculum] = useState(null);
  const [selectedMacro, setSelectedMacro] = useState(null);

  const fetchNextProblem = useCallback((currentSessionId) => {
    setFeedback(null);
    setUserAnswer('');
    setError(null);

    api.get('/problem/next', {
      params: {
        session_id: currentSessionId,
      },
    })
      .then((response) => {
        setProblem(response.data.problem);
        setGameState(response.data.state);
      })
      .catch((err) => {
        const errorMsg = err.response?.data?.detail || err.message || 'Failed to fetch problem';
        setError(errorMsg);
        console.error('Error fetching problem:', err);
      });
  }, []);

  useEffect(() => {
    let isMounted = true;

    const startSession = async () => {
      try {
        const curriculumResponse = await api.get('/curriculum');
        if (!isMounted) return;

        const availableMacros = curriculumResponse.data.macro_topics || [];
        if (availableMacros.length === 0) {
          throw new Error('No curriculum data available');
        }

        const initialMacro = availableMacros.includes(PREFERRED_MACRO)
          ? PREFERRED_MACRO
          : availableMacros[0];

        setCurriculum(curriculumResponse.data);
        setSelectedMacro(initialMacro);

        const sessionResponse = await api.post('/session/start', {
          username: DEFAULT_USERNAME,
          selected_macro: initialMacro,
        });
        if (!isMounted) return;

        setGameState(sessionResponse.data);
        setError(null);
        fetchNextProblem(sessionResponse.data.session_id);
      } catch (err) {
        if (!isMounted) return;
        const errorMsg = err.response?.data?.detail || err.message || 'Failed to start session';
        setError(errorMsg);
        console.error('Error starting session:', err);
      }
    };

    startSession();

    return () => {
      isMounted = false;
    };
  }, [fetchNextProblem]);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!gameState?.session_id || !problem?.problem_id || userAnswer.trim() === '') {
      return;
    }

    api.post('/problem/submit', {
      session_id: gameState.session_id,
      problem_id: problem.problem_id,
      user_input: userAnswer,
      is_text_mode: true,
    })
      .then((response) => {
        setGameState(response.data.state);
        setFeedback({
          correct: response.data.is_correct,
          message: response.data.feedback,
        });
        setError(null);
      })
      .catch((err) => {
        const errorMsg = err.response?.data?.detail || err.message || 'Failed to submit answer';
        setError(errorMsg);
        console.error('Error submitting answer:', err);
      });
  };

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 text-white p-8">
        <div className="max-w-md bg-red-900 border-2 border-red-600 rounded-lg p-6 text-center">
          <h2 className="text-2xl font-bold mb-4 text-red-200">Error</h2>
          <p className="text-lg mb-6">{error}</p>
          <button
            onClick={() => {
              setError(null);
              window.location.reload();
            }}
            className="bg-red-600 hover:bg-red-500 text-white px-6 py-2 rounded-lg font-bold"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!gameState) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 text-white">
        Connecting to Python Brain...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8 font-sans flex flex-col items-center">
      <div className="w-full max-w-2xl bg-slate-800 p-4 rounded-xl flex justify-between items-center shadow-lg mb-8 border border-slate-700">
        <div className="text-xl">
          XP: <span className="text-yellow-400 font-bold">{gameState.xp}</span>
        </div>
        <div className="text-xl">
          Streak: <span className="text-orange-400 font-bold">{gameState.streak} 🔥</span>
        </div>
        <div className="text-xl">
          Bonus:{' '}
          <span className={gameState.flawless_eligible ? 'text-green-400 font-bold' : 'text-red-500 font-bold'}>
            {gameState.flawless_eligible ? 'Active 💎' : 'Lost ❌'}
          </span>
        </div>
      </div>

      <div className="w-full max-w-2xl bg-slate-800 p-8 rounded-2xl shadow-2xl border border-slate-700 text-center">
        {problem ? (
          <>
            <div className="mb-6 text-slate-300">
              <p className="text-sm uppercase tracking-wide">{selectedMacro || gameState.selected_macro}</p>
              <h2 className="text-3xl font-medium">Solve this:</h2>
            </div>
            <div className="text-5xl font-bold mb-8 p-4 bg-slate-700 rounded-lg">
              <BlockMath math={problem.question} />
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col items-center gap-4">
              <input
                type="text"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder="Type your answer..."
                className="px-6 py-4 text-2xl text-black rounded-lg w-64 text-center focus:outline-none focus:ring-4 focus:ring-blue-500"
                autoFocus
                disabled={feedback !== null}
              />

              {!feedback ? (
                <button
                  type="submit"
                  disabled={userAnswer.trim() === ''}
                  className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg text-xl font-bold transition-all shadow-lg hover:shadow-blue-500/50"
                >
                  Submit Answer
                </button>
              ) : (
                <div className="w-full flex flex-col items-center gap-4 mt-4">
                  <div className={`text-2xl font-bold ${feedback.correct ? 'text-green-400' : 'text-red-400'}`}>
                    {feedback.message}
                  </div>
                  <button
                    type="button"
                    onClick={() => fetchNextProblem(gameState.session_id)}
                    className="bg-slate-700 hover:bg-slate-600 text-white px-8 py-3 rounded-lg text-xl font-bold transition-all"
                  >
                    Next Problem ➡️
                  </button>
                </div>
              )}
            </form>
          </>
        ) : (
          <div className="text-2xl text-slate-400 animate-pulse">
            Loading problem from {curriculum ? selectedMacro : 'curriculum'}...
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
