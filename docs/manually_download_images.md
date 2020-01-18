# Manually download images from the Intervalometerator

## What software to use?

<a href="https://filezilla-project.org/">_FileZilla_</a> is an open source FTP Client, distributed free of charge under the terms of the GNU General Public License.  
You can download and install _FileZilla_ for your operating system (Windows, Mac or Linux) from <a href="https://filezilla-project.org/download.php?show_all=1">here</a>.  

Other popular FTP Clients are [_WinSCP_](https://winscp.net/eng/index.php) for Windows or [_Cyberduck_](https://cyberduck.io/) for Mac - but in this example we'll use _FileZilla_ as it's platform-agnostic.

## Set up FileZilla
  
Run _FileZilla_ and Open the **Site Manager**. (**File** > **Site Manager** or the ![image](https://user-images.githubusercontent.com/44954153/72671179-7de8ba00-3a9a-11ea-8910-1eded8c17882.png) icon on the tool bar.)  
Click on the **New Site** button.  
Give the site a name. (I’ve creatively called mine “intvlm8r”.)  
Change the **Protocol** to SFTP.  
Input the IP address or host name of your Intervalometerator in the **Host** field.  
Leave the **Logon Type** as Normal.  
Add the **User**, which is the same as your Pi login – usually “pi”.  
Add the **Password** for the user.  
Click **OK**.  
  
A box may pop up asking if you want _FileZilla_ to remember passwords. I normally select "Save passwords" however you may elect not to save passwords or to set a master password in _FileZilla_, depending on your situation.
  
![Site Manager Screencap](https://user-images.githubusercontent.com/44954153/72656823-db74fc00-39f1-11ea-8ad4-d41ace72befd.png)
  
## Turn on the Intervalometerator
Either wait until the Intervalometerator turns the Raspberry Pi on at the hour set in the **System Maintenance Menu** or manually turn on the Pi using the enable switch.  
  
If you think you will need more time to download the images than the Intervalometerator usually stays on, it would be worthwhile changing the **Pi On** setting in the System Maintenance menu to its maximum value until you have finished. Don’t forget to change it back afterwards.  
  
![image](https://user-images.githubusercontent.com/44954153/72657155-f72dd180-39f4-11ea-8fbf-36437b884dd0.png)
  
## Connect to the Intervalometerator with FileZilla

> Note that if your Intervalometerator is configured as an access point, you will need to connect your computer to its network once it comes up.   
  
Open the **Site Manager** in _Filezilla_ and connect to the site you created earlier. Note that the first time you connect you will be prompted that the host key is unknown. Click the “Always trust this host” checkbox and then **OK**.  
  
![Unknown Host Key Screencap](https://user-images.githubusercontent.com/44954153/72657253-39a3de00-39f6-11ea-9524-f906056f7849.png)  
  
You should now be connected to the Intervalometerator. The left hand side of the screen in _FileZilla_ is the directory structure of your local machine and the right hand side is the directory structure of the Intervalometerator.  
  
![FileZilla Screencap](https://user-images.githubusercontent.com/44954153/72657266-61934180-39f6-11ea-99c4-fd7b3fef8b77.png)  
  
On the right hand side, navigate to the photos/DCIM folder and from there locate the images that you are after.  
On the left hand side, navigate to where you want to save the images on your local machine. (I created a folder called “intvlm8r Photos”.  
  
Now simply drag the images or folders that you want from the right hand side to the left or right-click on them and select **Download**. 
  
![FileZilla Screencap](https://user-images.githubusercontent.com/44954153/72657277-82f42d80-39f6-11ea-96f5-67b88e369e54.png)

At the bottom of _FileZilla_ you'll see three tabs. The number of images to be copied will show as "Queued Files", and this number should drop while the "Successful Transfers" count will increment. The area immediately above these tabs shows a more granular view of the transfer process.

Once all the images have transferred you can just close _FileZilla_.

> __At this stage__, there's no point deleting the files from the Pi, because they'll only be copied back across from the camera the next time the Pi boots. A pending update to the intvlm8r will address this by adding the option to delete the images from the camera once they're safely transferred to the Pi.  Keep an eye on [Issue #17](https://github.com/greiginsydney/Intervalometerator/issues/17) for movement on that front.


