import { DarkMode, LightMode } from '@mui/icons-material';
import { IconButton, Tooltip } from '@mui/material';
import type React from 'react';

interface ThemeSwitcherProps {
  mode: 'light' | 'dark';
  onToggleTheme: () => void;
}

const ThemeSwitcher: React.FC<ThemeSwitcherProps> = ({
  mode,
  onToggleTheme,
}) => {
  return (
    <Tooltip title={`Switch to ${mode === 'light' ? 'dark' : 'light'} theme`}>
      <IconButton
        onClick={onToggleTheme}
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          color: 'text.primary',
          backgroundColor: 'background.paper',
          border: '1px solid',
          borderColor: 'divider',
          '&:hover': {
            backgroundColor: 'action.hover',
          },
        }}
      >
        {mode === 'light' ? <DarkMode /> : <LightMode />}
      </IconButton>
    </Tooltip>
  );
};

export default ThemeSwitcher;
