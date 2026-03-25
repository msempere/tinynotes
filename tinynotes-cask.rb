cask "tinynotes" do
  version "1.0.0"
  sha256 "9bc0106b7f0d61de98639b1bab7ae14a2b7d03f529b24b67a8d6f94a314135f4"

  url "https://github.com/msempere/tinynotes/releases/download/v#{version}/TinyNotes-#{version}.zip"
  name "TinyNotes"
  desc "Simple macOS menu bar app for quick note-taking"
  homepage "https://github.com/msempere/tinynotes"

  livecheck do
    url :url
    strategy :github_latest
  end

  app "TinyNotes.app"

  postflight do
    system_command "/usr/bin/xattr",
                   args: ["-dr", "com.apple.quarantine", "#{appdir}/TinyNotes.app"],
                   sudo: false
  end

  zap trash: [
    "~/TinyNotes",
  ]
end
