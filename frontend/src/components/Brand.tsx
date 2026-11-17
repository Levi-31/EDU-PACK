import React from 'react';

const BRAND_PURPLE = '#916EED';

export const BrandMark: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    viewBox="0 0 56 60"
    fill="none"
    strokeWidth="3.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <polyline stroke={BRAND_PURPLE} points="12.7 39 4 43 28 56.5 52 43 43.3 39" />
    <polyline stroke={BRAND_PURPLE} points="12.7 26 4 30.5 28 44 52 30.5 43.3 26" />
    <polygon stroke="currentColor" points="28 3 52 17 28 31 4 17" />
  </svg>
);

export const BrandName: React.FC<{ stackOnMobile?: boolean }> = ({ stackOnMobile = false }) => (
  <>
    tokens<span style={{ color: BRAND_PURPLE }}>.to.</span>
    {stackOnMobile && <br className="sm:hidden" />}
    systems
  </>
);
