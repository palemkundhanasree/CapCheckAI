export interface DemoTestCase {
  id: string;
  type: 'claim' | 'url' | 'image' | 'video' | 'audio';
  title: string;
  badge: string;
  description: string;
  input: string;
  expectedVerdict: string;
}

export const DEMO_PRESETS: DemoTestCase[] = [
  {
    id: 'demo-bleach',
    type: 'claim',
    title: 'Drinking Disinfectant COVID Cure',
    badge: 'Contradicted',
    description: 'Viral claim asserting that ingesting household disinfectant or bleach destroys pathogens inside human lungs.',
    input: 'Drinking disinfectant or bleach is a proven medical cure for coronavirus infections and lung disease.',
    expectedVerdict: 'Contradicted / Likely False',
  },
  {
    id: 'demo-pope',
    type: 'claim',
    title: 'Pope Francis Balenciaga Puffer Coat',
    badge: 'AI-Generated',
    description: 'Photorealistic image showing Pope Francis walking the streets of Rome in an oversized designer puffer coat.',
    input: 'Pope Francis was photographed wearing a luxury white Balenciaga designer puffer jacket in Vatican City.',
    expectedVerdict: 'AI-Generated Media Detected',
  },
  {
    id: 'demo-moon',
    type: 'claim',
    title: 'Apollo 11 Moon Landing Staged',
    badge: 'Contradicted',
    description: 'Conspiracy claiming the Apollo 11 lunar module landing was filmed on a Hollywood soundstage by Stanley Kubrick.',
    input: 'The 1969 Apollo 11 moon landing was staged and filmed in a Hollywood studio rather than taking place on the Moon.',
    expectedVerdict: 'Contradicted / Likely False',
  },
  {
    id: 'demo-great-wall',
    type: 'claim',
    title: 'Great Wall Visible From Space',
    badge: 'Misleading Context',
    description: 'Popular claim that the Great Wall of China is the only man-made structure visible to astronaut naked eyes.',
    input: 'The Great Wall of China is the only man-made structure visible from space with the naked eye.',
    expectedVerdict: 'Misleading or Missing Context',
  },
  {
    id: 'demo-5g-birds',
    type: 'claim',
    title: '5G Towers Killing Birds',
    badge: 'Contradicted',
    description: 'Social media claim claiming 5G radio millimeter waves cause birds to fall dead from the sky in test cities.',
    input: '5G cell phone towers emit radiation that causes birds to fall dead from the sky in test cities.',
    expectedVerdict: 'Contradicted / Likely False',
  },
];
