import { Box } from '@mui/material';
import type React from 'react';
import logo from '../static/logo.png';

const FloatingLogo: React.FC = () => {
  return (
    <Box
      component="img"
      src={logo}
      alt="LiGre Logo"
      sx={{
        position: 'absolute',
        top: 16,
        left: 16,
        width: 64,
        height: 64,
      }}
    />
  );
};

export default FloatingLogo;
