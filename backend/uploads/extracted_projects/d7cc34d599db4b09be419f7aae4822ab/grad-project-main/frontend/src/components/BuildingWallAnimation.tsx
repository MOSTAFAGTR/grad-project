import React, { useState, useEffect } from 'react';

const COLUMNS = 10;
const ROWS = 7;
const TOTAL_BRICKS = COLUMNS * ROWS;
const STARTING_BRICKS = Math.ceil(TOTAL_BRICKS * 0.48);
const BRICK_INTERVAL = 1500; 

const BuildingWallAnimation: React.FC = () => {
  const [visibleCount, setVisibleCount] = useState(STARTING_BRICKS);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisibleCount((prev) => {
        if (prev < TOTAL_BRICKS) return prev + 1;
        clearInterval(interval);
        return prev;
      });
    }, BRICK_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  // Create rows bottom-up
  const rows: number[][] = [];
  for (let r = 0; r < ROWS; r++) {
    const start = r * COLUMNS;
    const row = Array.from({ length: COLUMNS }, (_, c) => start + c);
    rows.unshift(row);
  }

  return (
    <div
      className="flex flex-col gap-1"
      style={{
        width: 'min(95vw, 480px)',
        alignItems: 'center',
      }}
    >
      {rows.map((row, rowIndex) => (
        <div key={rowIndex} className="flex gap-1">
          {row.map((index) => (
            <div
              key={index}
              className={`brick ${index < visibleCount ? 'visible' : ''}`}
            />
          ))}
        </div>
      ))}

      <style>{`
        .brick {
          width: 45px;   /* Bigger width */
          height: 22px;  /* Bigger height */
          background-color: #fb923c;
          border: 1px solid #4a2a13;
          border-radius: 3px;
          opacity: 0;
          transform: translateY(30px) scale(0.5);
        }

        .brick.visible {
          animation: place-brick 0.9s forwards ease-out;
        }

        @keyframes place-brick {
          0% {
            opacity: 0;
            transform: translateY(30px) scale(0.5);
          }
          30% {
            opacity: 1;
            transform: translateY(0) scale(1.1);
            box-shadow: 0 0 8px rgba(255, 150, 80, 0.6);
          }
          100% {
            opacity: 1;
            transform: scale(1);
            box-shadow: none;
          }
        }
      `}</style>
    </div>
  );
};

export default BuildingWallAnimation;
