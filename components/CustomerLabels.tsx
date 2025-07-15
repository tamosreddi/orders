import React from 'react';
import { CustomerLabel } from '../types/customer';

interface CustomerLabelsProps {
  labels: CustomerLabel[];
  maxDisplay?: number;
}

export function CustomerLabels({ labels, maxDisplay = 2 }: CustomerLabelsProps) {
  if (labels.length === 0) {
    return <div className="text-gray-400 text-sm">-</div>;
  }

  const displayLabels = labels.slice(0, maxDisplay);
  const remainingCount = labels.length - maxDisplay;

  return (
    <div className="flex flex-wrap gap-1">
      {displayLabels.map((label) => (
        <div
          key={label.id}
          className="inline-flex items-center px-2 py-1 rounded text-xs font-medium"
          style={{ backgroundColor: label.color }}
        >
          {label.name}
          {label.value && (
            <span className="ml-1 text-xs opacity-75">
              {label.value}
            </span>
          )}
        </div>
      ))}
      {remainingCount > 0 && (
        <div className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600">
          +{remainingCount}
        </div>
      )}
    </div>
  );
}