import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';

type GameRow = {
  game_id: number;
  challenge_id: number;
  challenge_name: string;
  status: string;
  started_at: string;
  my_team: 'red' | 'blue';
  my_team_name: string;
  opponent_team_name: string;
  my_score: number;
  opponent_score: number;
  red_score: number;
  blue_score: number;
  red_team_name: string;
  blue_team_name: string;
};

const RedBlueMyGamesPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [games, setGames] = useState<GameRow[]>([]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    api
      .get('/api/redblue/my-games')
      .then((res) => {
        if (!cancelled) setGames(res.data?.games || []);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-8">
        <div className="h-10 w-10 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-8">
        <p className="text-red-300">Could not load your games. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 md:p-10">
      <h1 className="text-3xl font-bold text-white mb-2">My Red vs Blue Games</h1>
      <p className="text-gray-400 mb-8">Games assigned to you by your instructor.</p>

      {games.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div
            className="mb-6"
            style={{
              width: 80,
              height: 88,
              background: 'linear-gradient(145deg, #374151 0%, #1f2937 100%)',
              clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
              border: '2px solid #6b7280',
            }}
            aria-hidden
          />
          <p className="text-xl font-semibold text-gray-200">No games yet</p>
          <p className="text-gray-500 mt-2 max-w-md">
            Your instructor hasn&apos;t assigned you to a Red vs Blue game yet. Check back later.
          </p>
        </div>
      ) : (
        <div className="grid gap-6 max-w-3xl">
          {games.map((g) => {
            const isActive = g.status === 'active';
            const isRed = g.my_team === 'red';
            return (
              <div
                key={g.game_id}
                className="rounded-xl border border-gray-700 bg-gray-800/80 overflow-hidden shadow-lg"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-b border-gray-700">
                  <span className="font-bold text-lg text-white">{g.challenge_name}</span>
                  {isActive ? (
                    <span className="inline-flex items-center gap-2 text-sm font-semibold text-emerald-400">
                      <span className="relative flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
                      </span>
                      ACTIVE
                    </span>
                  ) : (
                    <span className="text-sm font-medium text-gray-500 uppercase">COMPLETED</span>
                  )}
                </div>

                <div
                  className={`px-4 py-3 text-sm ${
                    isRed ? 'bg-red-950/50 border-l-4 border-red-500' : 'bg-blue-950/50 border-l-4 border-blue-500'
                  }`}
                >
                  {isRed ? (
                    <>
                      <p className="font-semibold text-red-200">
                        You are on the RED TEAM — {g.my_team_name}
                      </p>
                      <p className="text-red-100/90 mt-1">Your mission: exploit the challenge vulnerability</p>
                      <p className="mt-2 font-mono text-red-300">
                        Your score: {g.my_score} attacks
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="font-semibold text-blue-200">
                        You are on the BLUE TEAM — {g.my_team_name}
                      </p>
                      <p className="text-blue-100/90 mt-1">Your mission: detect attacks and submit fixes</p>
                      <p className="mt-2 font-mono text-blue-300">
                        Your score: {g.my_score} fixes
                      </p>
                    </>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2 px-4 py-3 bg-gray-900/50">
                  <div
                    className={`rounded-lg p-3 border ${
                      isRed ? 'border-red-600 bg-red-950/30' : 'border-gray-700'
                    }`}
                  >
                    <p className={`text-xs text-gray-400 mb-1 ${isRed ? 'font-bold text-red-200' : ''}`}>
                      {g.red_team_name || 'Red'}
                    </p>
                    <p className={`text-lg ${isRed ? 'font-bold text-white' : 'text-gray-300'}`}>
                      {g.red_score}
                    </p>
                  </div>
                  <div
                    className={`rounded-lg p-3 border ${
                      !isRed ? 'border-blue-600 bg-blue-950/30' : 'border-gray-700'
                    }`}
                  >
                    <p className={`text-xs text-gray-400 mb-1 ${!isRed ? 'font-bold text-blue-200' : ''}`}>
                      {g.blue_team_name || 'Blue'}
                    </p>
                    <p className={`text-lg ${!isRed ? 'font-bold text-white' : 'text-gray-300'}`}>
                      {g.blue_score}
                    </p>
                  </div>
                </div>

                <div className="p-4 pt-0">
                  <button
                    type="button"
                    onClick={() => navigate(`/redblue/game/${g.game_id}`)}
                    className={`w-full py-3 rounded-lg font-bold transition ${
                      isActive
                        ? 'bg-purple-600 hover:bg-purple-500 text-white'
                        : 'bg-transparent border border-gray-500 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {isActive ? 'Enter Game' : 'View Results'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default RedBlueMyGamesPage;
