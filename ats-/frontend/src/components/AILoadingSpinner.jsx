import React from 'react';
import { motion } from 'framer-motion';
import { 
  CpuChipIcon, 
  MagnifyingGlassIcon, 
  DocumentTextIcon,
  SparklesIcon 
} from '@heroicons/react/24/outline';

const AILoadingSpinner = ({ 
  size = 'lg',
  message = "Our AI is checking and matching resumes from your database so please wait it may take some time.",
  showIcon = true 
}) => {
  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-20 h-20',
    lg: 'w-24 h-24',
    xl: 'w-32 h-32'
  };

  const iconSizes = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
    xl: 'w-12 h-12'
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-6 py-8">
      {/* Main AI Loading Animation */}
      <div className="relative">
        {/* Outer rotating ring */}
        <motion.div
          className={`${sizeClasses[size]} border-4 border-blue-200 border-t-blue-600 rounded-full`}
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        />
        
        {/* Inner pulsing core */}
        <motion.div
          className={`${sizeClasses[size]} absolute inset-0 border-4 border-purple-200 border-t-purple-600 rounded-full`}
          animate={{ rotate: -360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
        />
        
        {/* Center AI icon */}
        {showIcon && (
          <motion.div
            className="absolute inset-0 flex items-center justify-center"
            animate={{ 
              scale: [1, 1.1, 1],
              opacity: [0.8, 1, 0.8]
            }}
            transition={{ 
              duration: 2, 
              repeat: Infinity, 
              ease: "easeInOut" 
            }}
          >
            <CpuChipIcon className={`${iconSizes[size]} text-blue-600`} />
          </motion.div>
        )}
        
        {/* Floating particles */}
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full"
            style={{
              top: `${50 + 40 * Math.cos(i * Math.PI / 3)}%`,
              left: `${50 + 40 * Math.sin(i * Math.PI / 3)}%`,
            }}
            animate={{
              scale: [0, 1, 0],
              opacity: [0, 1, 0],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              delay: i * 0.3,
              ease: "easeInOut"
            }}
          />
        ))}
      </div>

      {/* AI Processing Message */}
      <div className="text-center space-y-3 max-w-md">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex items-center justify-center space-x-2 text-blue-600"
        >
          <SparklesIcon className="w-5 h-5" />
          <span className="text-sm font-semibold">AI Processing</span>
          <SparklesIcon className="w-5 h-5" />
        </motion.div>
        
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="text-sm text-gray-600 leading-relaxed"
        >
          {message}
        </motion.p>
        
        {/* Animated dots */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="flex justify-center space-x-1"
        >
          {[...Array(3)].map((_, i) => (
            <motion.div
              key={i}
              className="w-2 h-2 bg-blue-500 rounded-full"
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut"
              }}
            />
          ))}
        </motion.div>
      </div>

      {/* Scanning animation */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 1.2 }}
        className="flex items-center space-x-3 text-xs text-gray-500"
      >
        <motion.div
          animate={{ x: [-10, 10, -10] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <MagnifyingGlassIcon className="w-4 h-4 text-blue-500" />
        </motion.div>
        <span>Scanning database</span>
        <motion.div
          animate={{ x: [-10, 10, -10] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
        >
          <DocumentTextIcon className="w-4 h-4 text-purple-500" />
        </motion.div>
        <span>Analyzing resumes</span>
      </motion.div>
    </div>
  );
};

export default AILoadingSpinner;
