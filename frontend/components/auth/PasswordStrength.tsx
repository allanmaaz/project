import React from "react";

interface PasswordStrengthProps {
  score: number; // 0 to 4
}

export default function PasswordStrength({ score }: PasswordStrengthProps) {
  const getStrengthLabel = () => {
    switch (score) {
      case 0:
        return "Very Weak";
      case 1:
        return "Weak";
      case 2:
        return "Fair";
      case 3:
        return "Strong";
      case 4:
        return "Very Strong";
      default:
        return "Weak";
    }
  };

  const getStrengthColor = () => {
    switch (score) {
      case 0:
        return "bg-danger-500";
      case 1:
        return "bg-danger-500";
      case 2:
        return "bg-warning-500";
      case 3:
        return "bg-brand-500";
      case 4:
        return "bg-success-500";
      default:
        return "bg-muted";
    }
  };

  return (
    <div className="mt-2 w-full">
      <div className="flex justify-between items-center mb-1">
        <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">
          Password Strength
        </span>
        <span className="text-[10px] font-bold text-muted-foreground">{getStrengthLabel()}</span>
      </div>
      <div className="grid grid-cols-4 gap-1">
        {[1, 2, 3, 4].map((index) => (
          <div
            key={index}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              index <= score ? getStrengthColor() : "bg-neutral-200 dark:bg-neutral-800"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
