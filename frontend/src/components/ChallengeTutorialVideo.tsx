import React from 'react';
import { getChallengeTutorialVideoUrl } from '../lib/challengeTutorialVideos';

type Props = {
  challengeId: number;
  className?: string;
};

/**
 * HTML5 player for the voiced tutorial tied to a SCALE challenge (1–10).
 */
const ChallengeTutorialVideo: React.FC<Props> = ({ challengeId, className = '' }) => {
  const src = getChallengeTutorialVideoUrl(challengeId);
  if (!src) return null;

  return (
    <div
      className={`w-full max-w-4xl mx-auto rounded-lg overflow-hidden border-2 border-gray-700 bg-black/40 ${className}`}
    >
      <video
        className="w-full h-auto max-h-[75vh] object-contain bg-black"
        controls
        playsInline
        preload="metadata"
        src={src}
      >
        Your browser does not support the video tag.
      </video>
    </div>
  );
};

export default ChallengeTutorialVideo;
