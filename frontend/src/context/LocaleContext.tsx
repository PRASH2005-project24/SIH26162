import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useState, useEffect } from 'react';

interface LocaleContextProps {
  locale: 'en' | 'hi';
  toggleLocale: () => void;
  t: (key: string) => string;
}

const LocaleContext = createContext<LocaleContextProps | undefined>(undefined);

// Define the translation type to ensure both English and Hindi objects have the same keys
type Translation = {
  appTitle: string;
  dashboard: string;
  liveEvents: string;
  historicalEvents: string;
  analytics: string;
  settings: string;
  mapLayers: string;
  satellite: string;
  terrain: string;
  political: string;
  timeRange: string;
  today: string;
  last24Hours: string;
  last7Days: string;
  last30Days: string;
  custom: string;
  categories: string;
  industrialFire: string;
  wildfireNaturalFire: string;
  agriculturalFire: string;
  persistentThermalSource: string;
  unknownOther: string;
  eventDetails: string;
  firmsData: string;
  osmContext: string;
  dynamicWorldLandCover: string;
  persistenceAnalysis: string;
  mlClassification: string;
  acquisitionTime: string;
  satelliteLabel: string;
  dayNight: string;
  status: string;
  confidence: string;
  brightnessTemperature: string;
  fireRadiativePower: string;
  insideIndustrialZone: string;
  nearestFeatureDistance: string;
  featureCount1km: string;
  nearbyWater: string;
  label: string;
  acquisitionDate: string;
  queryDate: string;
  coverageState: string;
  classProbabilities: string;
  isPersistent: string;
  observationDates: string;
  duration: string;
  totalDetections: string;
  activeDetections: string;
  enrichedEvents: string;
  highRisk: string;
  categoryBreakdown: string;
  satelliteData: string;
  averageConfidence: string;
  averageFrp: string;
  additionalMetrics: string;
  loading: string;
  error: string;
  noEventsFound: string;
  noDataAvailable: string;
  theme: string;
  language: string;
  mapPreferences: string;
  demoLiveStatus: string;
  close: string;
  apply: string;
  cancel: string;
  save: string;
  live: string;
};

// Simple translation object - in a real app, you might load these from JSON files
const translations = {
  en: {
    // Common
    appTitle: 'FireGuard',
    dashboard: 'Dashboard',
    liveEvents: 'Live Events',
    historicalEvents: 'Historical Events',
    analytics: 'Analytics',
    settings: 'Settings',

    // Map
    mapLayers: 'Map Layers',
    satellite: 'Satellite',
    terrain: 'Terrain',
    political: 'Political',

    // Time filters
    timeRange: 'Time Range',
    today: 'Today',
    last24Hours: 'Last 24 Hours',
    last7Days: 'Last 7 Days',
    last30Days: 'Last 30 Days',
    custom: 'Custom',

    // Categories
    categories: 'Categories',
    industrialFire: 'Industrial Fire',
    wildfireNaturalFire: 'Wildfire / Natural Fire',
    agriculturalFire: 'Agricultural Fire',
    persistentThermalSource: 'Persistent Thermal Source',
    unknownOther: 'Unknown / Other',

    // Event details
    eventDetails: 'Event Details',
    firmsData: 'FIRMS Data',
    osmContext: 'OSM Context',
    dynamicWorldLandCover: 'Dynamic World Land Cover',
    persistenceAnalysis: 'Persistence Analysis',
    mlClassification: 'ML Classification',

    // FIRMS
    acquisitionTime: 'Acquisition Time',
    satelliteLabel: 'Satellite',
    dayNight: 'Day/Night',
    status: 'Status',
    confidence: 'Confidence',
    brightnessTemperature: 'Brightness Temperature',
    fireRadiativePower: 'Fire Radiative Power (FRP)',

    // OSM
    insideIndustrialZone: 'Inside Industrial Zone',
    nearestFeatureDistance: 'Nearest Feature Distance',
    featureCount1km: 'Feature Count (1km)',
    nearbyWater: 'Nearby Water',

    // Dynamic World
    label: 'Label',
    acquisitionDate: 'Acquisition Date',
    queryDate: 'Query Date',
    coverageState: 'Coverage State',
    classProbabilities: 'Class Probabilities',

    // Persistence
    isPersistent: 'Is Persistent',
    observationDates: 'Observation Dates',
    duration: 'Duration',

    // Statistics
    totalDetections: 'Total Detections',
    activeDetections: 'Active Detections',
    enrichedEvents: 'Enriched Events',
    highRisk: 'High Risk',
    categoryBreakdown: 'Category Breakdown',
    satelliteData: 'Satellite Data',
    averageConfidence: 'Average Confidence',
    averageFrp: 'Average FRP',
    additionalMetrics: 'Additional Metrics',

    // Loading states
    loading: 'Loading...',
    error: 'Error',
    noEventsFound: 'No events found',
    noDataAvailable: 'No data available',

    // Settings
    theme: 'Theme',
    language: 'Language',
    mapPreferences: 'Map Preferences',
    demoLiveStatus: 'Demo/Live Status',

    // Buttons
    close: 'Close',
    apply: 'Apply',
    cancel: 'Cancel',
    save: 'Save',
    live: 'Live'
  } as Translation,
  hi: {
    // Common
    appTitle: 'ファイアーガード',
    dashboard: 'ダッシュボード',
    liveEvents: 'ライブイベント',
    historicalEvents: 'ヒストリカルイベント',
    analytics: 'アナリティクス',
    settings: '設定',

    // Map
    mapLayers: 'マップレイヤー',
    satellite: '衛星',
    terrain: '地形',
    political: '政治',

    // Time filters
    timeRange: '時間範囲',
    today: '今日',
    last24Hours: '過去24時間',
    last7Days: '過去7日',
    last30Days: '過去30日',
    custom: 'カスタム',

    // Categories
    categories: 'カテゴリー',
    industrialFire: '産業火災',
    wildfireNaturalFire: '野火/自然火災',
    agriculturalFire: '農業火災',
    persistentThermalSource: '持続的熱源',
    unknownOther: '不明/その他',

    // Event details
    eventDetails: 'イベント詳細',
    firmsData: 'FIRMSデータ',
    osmContext: 'OSMコンテキスト',
    dynamicWorldLandCover: 'Dynamic World Land Cover',
    persistenceAnalysis: '永続性分析',
    mlClassification: 'ML分類',

    // FIRMS
    acquisitionTime: '取得時間',
    satelliteLabel: '衛星',
    dayNight: '昼/夜',
    status: '状態',
    confidence: '信頼度',
    brightnessTemperature: '明るさ温度',
    fireRadiativePower: '火災放射パワー (FRP)',

    // OSM
    insideIndustrialZone: '産業地域内',
    nearestFeatureDistance: '最寄りの特徴距離',
    featureCount1km: '1km内の特徴数',
    nearbyWater: '近くの水',

    // Dynamic World
    label: 'ラベル',
    acquisitionDate: '取得日',
    queryDate: 'クエリー日',
    coverageState: 'カバレッジ状態',
    classProbabilities: 'クラス確率',

    // Persistence
    isPersistent: '永続的か',
    observationDates: '観測日',
    duration: '期間',

    // Statistics
    totalDetections: '総検出数',
    activeDetections: 'アクティブ検出数',
    enrichedEvents: 'エンリッチドイベント数',
    highRisk: 'ハイリスク',
    categoryBreakdown: 'カテゴリー内訳',
    satelliteData: '衛星データ',
    averageConfidence: '平均信頼度',
    averageFrp: '平均FRP',
    additionalMetrics: '追加メトリクス',

    // Loading states
    loading: '読み込み中...',
    error: 'エラー',
    noEventsFound: 'イベントが見つかりません',
    noDataAvailable: 'データが利用できません',

    // Settings
    theme: 'テーマ',
    language: '言語',
    mapPreferences: 'マップ設定',
    demoLiveStatus: 'デモ/ライブ状態',

    // Buttons
    close: '閉じる',
    apply: '適用',
    cancel: 'キャンセル',
    save: '保存',
    live: 'ライブ'
  } as Translation
};

export const useLocale = () => {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error('useLocale must be used within a LocaleProvider');
  }
  return context;
};

interface LocaleProviderProps {
  children: ReactNode;
}

export const LocaleProvider = ({ children }: LocaleProviderProps) => {
  const [locale, setLocale] = useState<'en' | 'hi'>(() => {
    // Check for saved locale preference or use browser language
    const savedLocale = localStorage.getItem('locale') as 'en' | 'hi' | null;
    if (savedLocale && (savedLocale === 'en' || savedLocale === 'hi')) {
      return savedLocale;
    }

    // Check browser language
    if (typeof window !== 'undefined') {
      const browserLang = navigator.language.substring(0, 2) as 'en' | 'hi' | undefined;
      if (browserLang === 'hi') {
        return 'hi';
      }
    }

    return 'en'; // default
  });

  useEffect(() => {
    // Save locale preference
    localStorage.setItem('locale', locale);
  }, [locale]);

  const toggleLocale = () => {
    setLocale(prevLocale => (prevLocale === 'en' ? 'hi' : 'en'));
  };

  const t = (key: string): string => {
    return (translations[locale as keyof typeof translations] as Translation)[key as keyof Translation] || key;
  };

  return (
    <LocaleContext.Provider value={{ locale, toggleLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
};