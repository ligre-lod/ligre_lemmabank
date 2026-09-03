import {
  Box,
  Button,
  Menu,
  MenuItem,
  CircularProgress,
} from '@mui/material';
import { ArrowDropDown } from '@mui/icons-material';
import React, { useEffect, useState, useCallback } from 'react';
import { getRuntimeConfig } from '../utils/config';

interface GitHubRepo {
  name: string;
  html_url: string;
  homepage: string | null;
  description: string | null;
  topics: string[];
}

interface MenuItemData {
  label: string;
  href: string;
  key?: string;
}

interface ButtonMenuProps {
  label: string;
  items: MenuItemData[];
  loading?: boolean;
  emptyMessage?: string;
}

const ButtonMenu: React.FC<ButtonMenuProps> = ({
  label,
  items,
  loading = false,
  emptyMessage = 'No items found',
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = useCallback((event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  }, []);

  const handleClose = useCallback(() => {
    setAnchorEl(null);
  }, []);

  return (
    <>
      <Button
        onClick={handleClick}
        endIcon={<ArrowDropDown />}
        sx={{
          color: 'inherit',
          textTransform: 'none',
          fontSize: '0.875rem',
          opacity: 0.8,
          minWidth: 'auto',
          padding: '0 4px',
          '&:hover': {
            opacity: 1,
            backgroundColor: 'transparent',
          },
        }}
      >
        {label}
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'center',
        }}
      >
        {loading ? (
          <MenuItem disabled>
            <CircularProgress size={20} sx={{ mr: 1 }} />
            Loading...
          </MenuItem>
        ) : items.length === 0 ? (
          <MenuItem disabled>{emptyMessage}</MenuItem>
        ) : (
          items.map((item) => (
            <MenuItem
              key={item.key || item.href}
              component="a"
              href={item.href}
              target="_blank"
              rel="noopener noreferrer"
              onClick={handleClose}
            >
              {item.label}
            </MenuItem>
          ))
        )}
      </Menu>
    </>
  );
};

const NavigationLinks: React.FC = () => {
  const [ligreTools, setLiitaTools] = useState<GitHubRepo[]>([]);
  const [loading, setLoading] = useState(true);
  const [sparqlEndpointUrl, setSparqlEndpointUrl] = useState<string | null>(
    null,
  );

  useEffect(() => {
    getRuntimeConfig().then((config) =>
      setSparqlEndpointUrl(config.sparqlEndpointUrl),
    );
  }, []);

  useEffect(() => {
    const fetchLiitaTools = async () => {
      try {
        const response = await fetch('https://api.github.com/users/LiGre-LOD/repos');
        if (!response.ok) {
          throw new Error('Failed to fetch repositories');
        }
        const repos: GitHubRepo[] = await response.json();
        const filteredRepos = repos.filter((repo) =>
          repo.topics.includes('ligre-toolkit')
        );
        // Sort by name alphabetically
        filteredRepos.sort((a, b) => a.name.localeCompare(b.name));
        setLiitaTools(filteredRepos);
      } catch (error) {
        console.error('Error fetching LiGre tools:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLiitaTools();
  }, []);

  const getRepoUrl = (repo: GitHubRepo): string => {
    return repo.homepage || repo.html_url;
  };

  const toolkitItems: MenuItemData[] = [
    ...(sparqlEndpointUrl
      ? [{ label: 'SPARQL Endpoint', href: sparqlEndpointUrl, key: 'sparql-endpoint' }]
      : []),
    ...ligreTools.map((repo) => ({
      label: repo.description || repo.name,
      href: getRepoUrl(repo),
      key: repo.name,
    })),
  ];

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 6 }}>
      {/*<Link*/}
      {/*  href="https://ligre.it"*/}
      {/*  target="_blank"*/}
      {/*  rel="noopener noreferrer"*/}
      {/*  sx={{*/}
      {/*    color: 'inherit',*/}
      {/*    textDecoration: 'none',*/}
      {/*    fontSize: '0.875rem',*/}
      {/*    opacity: 0.8,*/}
      {/*    '&:hover': {*/}
      {/*      opacity: 1,*/}
      {/*      textDecoration: 'underline',*/}
      {/*    },*/}
      {/*  }}*/}
      {/*>*/}
      {/*  Back to Home*/}
      {/*</Link>*/}
      <ButtonMenu
        label="LiGre Toolkit"
        items={toolkitItems}
        loading={loading}
        emptyMessage="No tools found"
      />
    </Box>
  );
};

export default NavigationLinks;
