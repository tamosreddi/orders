//used in Customers page to display the customer labels

import React from 'react';
import { CustomerLabel } from '../../types/customer';

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
          className="inline-flex items-center px-2 py-1 rounded text-sm font-normal"
          style={{ backgroundColor: label.color }}
        >
          {label.name}
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