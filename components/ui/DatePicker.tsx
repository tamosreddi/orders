'use client';

import React, { useState } from 'react';
import DatePickerReact from 'react-datepicker';
import { registerLocale, setDefaultLocale } from 'react-datepicker';
import { es } from 'date-fns/locale/es';
import 'react-datepicker/dist/react-datepicker.css';

// Register Spanish locale
registerLocale('es', es);

interface DatePickerProps {
  selected?: Date | null;
  onChange: (date: Date | null) => void;
  placeholderText?: string;
  className?: string;
  dateFormat?: string;
  disabled?: boolean;
}

export function DatePicker({
  selected,
  onChange,
  placeholderText = "Seleccionar fecha",
  className = "",
  dateFormat = "dd/MM/yyyy",
  disabled = false
}: DatePickerProps) {
  return (
    <div className="relative">
      <DatePickerReact
        selected={selected}
        onChange={onChange}
        locale="es"
        dateFormat={dateFormat}
        placeholderText={placeholderText}
        disabled={disabled}
        className={`px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${className}`}
        calendarClassName="shadow-lg border border-gray-200 rounded-lg"
        popperClassName="!z-[9999]"
        showPopperArrow={false}
        autoComplete="off"
        withPortal
        portalId="react-datepicker-portal"
      />
    </div>
  );
}